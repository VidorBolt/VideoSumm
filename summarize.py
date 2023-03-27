import pytube
import moviepy.editor as mp
import os
import openai
import time

Language = "English"
def extract_audio(url, output_path):
    youtube = pytube.YouTube(url)
    video = youtube.streams.filter(only_audio=True).first()
    video.download(output_path=output_path, filename='audio.mp4')

    video_path = output_path + '/audio.mp4'
    audio_path = output_path + '/audio.mp3'
    clip = mp.AudioFileClip(video_path)
    clip.write_audiofile(audio_path)

    clip.close()
    os.remove(video_path)


def transcribe_audio(openai_api_key, whisper_model, audio_file):
    openai.api_key = openai_api_key

    retries = 5
    backoff_factor = 2
    sleep_time = 1

    for retry_attempt in range(retries):
        try:
            response = openai.Audio.transcribe(whisper_model, audio_file)
            return response.get("text")
        except openai.error.RateLimitError:
            if retry_attempt + 1 == retries:
                raise
            time.sleep(sleep_time)
            sleep_time *= backoff_factor

def chat_gpt_response(message_text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI that takes transcripts of YouTube videos in 10,000-word intervals and extracts the most important information from them, providing a summarized version in a clear and concise format. Your task is to analyze the given transcript segments, identify the key points, and present them in an organized manner that is easy to understand. You should be able to capture the essence of the video while eliminating any unnecessary or repetitive content. When you receive a transcript segment, process the content and wait for the next segment. Continue processing segments until you receive an input containing <end>. Once you receive the final input with <end>, deliver a comprehensive summary that highlights the main points and valuable insights from the entire video. If language is not in English change to English"},
            {"role": "user", "content": message_text}
        ]
    )

    return response['choices'][0]['message']['content']

def word_count(s):
    return len(s.split())

def process_string(s, interval=7000):
    words = s.split()
    total_words = len(words)

    for i in range(0, total_words, interval):
        segment = words[i:i + interval]
        if i + interval >= total_words:
            segment.append('<end>')
        process_segment(segment)

def process_segment(segment):
    return chat_gpt_response(segment)

def split_audio_file(audio_path, output_path, num_segments):
    clip = mp.AudioFileClip(audio_path)
    duration = clip.duration
    segment_duration = duration / num_segments

    start_time = 0
    end_time = 0
    counter = 0
    audio_files = []

    while end_time < duration:
        end_time += segment_duration
        if end_time > duration:
            end_time = duration

        output_filename = f"{output_path}/split_audio_{counter}.mp3"
        subclip = clip.subclip(start_time, end_time)
        subclip.write_audiofile(output_filename)
        audio_files.append(output_filename)

        start_time = end_time
        counter += 1

    clip.close()

    return audio_files

def main(url):
    openai_api_key = "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"
    whisper_model = "whisper-1"
    output_path = r"C:\Users\ahmad\PycharmProjects\ChatGpt"
    audio_path = output_path + r'\audio.mp3'
    num_segments = 4

    extract_audio(url, output_path)

    audio_size = os.path.getsize(audio_path)
    if audio_size > 25 * 1024 * 1024:
        audio_files = split_audio_file(audio_path, output_path, num_segments)
    else:
        audio_files = [audio_path]

    combined_summary = ''
    for audio_file in audio_files:
        with open(audio_file, 'rb') as audio_file_obj:
            transcription = transcribe_audio(openai_api_key, whisper_model, audio_file_obj)

        if word_count(transcription) > 7000:
            process_string(transcription)
        else:
            summary = chat_gpt_response(transcription)
            combined_summary += summary + '\n\n'

        #os.remove(audio_file)

    #os.remove(audio_path)
    return combined_summary

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
