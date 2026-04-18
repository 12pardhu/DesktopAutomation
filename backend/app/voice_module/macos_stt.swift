import Foundation
import Speech

struct TranscriptionResult: Codable {
    let transcript: String
    let detected_language: String
    let error: String?
}

func authorizeSpeech() -> SFSpeechRecognizerAuthorizationStatus {
    let semaphore = DispatchSemaphore(value: 0)
    var authStatus: SFSpeechRecognizerAuthorizationStatus = .notDetermined
    SFSpeechRecognizer.requestAuthorization { status in
        authStatus = status
        semaphore.signal()
    }
    semaphore.wait()
    return authStatus
}

func transcribe(url: URL, localeIdentifier: String) -> String? {
    guard let recognizer = SFSpeechRecognizer(locale: Locale(identifier: localeIdentifier)) else {
        return nil
    }
    guard recognizer.isAvailable else {
        return nil
    }

    let request = SFSpeechURLRecognitionRequest(url: url)
    request.requiresOnDeviceRecognition = true
    request.shouldReportPartialResults = false

    let semaphore = DispatchSemaphore(value: 0)
    var finalText: String?
    var finalError: Error?

    let task = recognizer.recognitionTask(with: request) { result, error in
        if let result = result, result.isFinal {
            finalText = result.bestTranscription.formattedString
            semaphore.signal()
            return
        }
        if let error = error {
            finalError = error
            semaphore.signal()
        }
    }

    let timeout = DispatchTime.now() + .seconds(45)
    _ = semaphore.wait(timeout: timeout)
    task.cancel()

    if finalText?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty == false {
        return finalText
    }
    if finalError != nil {
        return nil
    }
    return nil
}

let arguments = CommandLine.arguments
guard arguments.count >= 2 else {
    let payload = TranscriptionResult(transcript: "", detected_language: "en", error: "Missing audio file path.")
    let data = try! JSONEncoder().encode(payload)
    FileHandle.standardOutput.write(data)
    exit(1)
}

let audioURL = URL(fileURLWithPath: arguments[1])
let localesArgument = arguments.count >= 3 ? arguments[2] : "en-US,hi-IN,te-IN"
let locales = localesArgument.split(separator: ",").map { String($0) }

let authStatus = authorizeSpeech()
guard authStatus == .authorized else {
    let payload = TranscriptionResult(
        transcript: "",
        detected_language: "en",
        error: "Speech recognition permission was not granted for this app or terminal."
    )
    let data = try! JSONEncoder().encode(payload)
    FileHandle.standardOutput.write(data)
    exit(2)
}

for locale in locales {
    if let transcript = transcribe(url: audioURL, localeIdentifier: locale) {
        let payload = TranscriptionResult(transcript: transcript, detected_language: locale, error: nil)
        let data = try! JSONEncoder().encode(payload)
        FileHandle.standardOutput.write(data)
        exit(0)
    }
}

let payload = TranscriptionResult(
    transcript: "",
    detected_language: locales.first ?? "en-US",
    error: "No on-device transcription was produced. Make sure Dictation/Speech assets are available on this Mac."
)
let data = try! JSONEncoder().encode(payload)
FileHandle.standardOutput.write(data)
exit(3)
