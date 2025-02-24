import streamlit as st
import subprocess
import os

def convert_vtt_to_ass(vtt_path, ass_path):
    ass_template = """[Script Info]
Title: Styled Subtitles
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Nunito,62,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,10,10,490,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def convert_time(vtt_time):
        h, m, s = vtt_time.split(":")
        s, ms = s.split(".")
        ms = ms[:2]
        return f"{h}:{m}:{s}.{ms}"

    with open(vtt_path, "r", encoding="utf-8") as vtt, open(ass_path, "w", encoding="utf-8") as ass:
        ass.write(ass_template)
        lines = vtt.readlines()

        for i in range(len(lines)):
            if "-->" in lines[i]:
                start, end = lines[i].strip().split(" --> ")
                start = convert_time(start)
                end = convert_time(end)
                text = lines[i + 1].strip() if i + 1 < len(lines) else ''

                effect = "{\\fad(500,500)}"

                if text:
                    ass.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{effect}{text}\n")

def burn_subtitles_with_background(vtt_file, background_image, audio_file, output_video):
    ass_file = "converted_subtitles.ass"
    convert_vtt_to_ass(vtt_file, ass_file)

    temp_bg_video = "temp_background.mp4"
    temp_final_video = "temp_final.mp4"

    create_bg_command = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", background_image,
        "-c:v", "libx264",
        "-t", "3:14",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-pix_fmt", "yuv420p",
        temp_bg_video
    ]

    subprocess.run(create_bg_command, check=True)

    burn_subs_command = [
        "ffmpeg", "-y",
        "-i", temp_bg_video,
        "-vf", f"ass={ass_file}",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        temp_final_video
    ]
    subprocess.run(burn_subs_command, check=True)

    add_audio_command = [
        "ffmpeg", "-y",
        "-i", temp_final_video,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_video
    ]
    subprocess.run(add_audio_command, check=True)

    os.remove(temp_bg_video)
    os.remove(temp_final_video)
    os.remove(ass_file)

# Streamlit UI
st.title("Video Generator")

vtt_file = st.file_uploader("Upload Subtitle File (.vtt)", type=["vtt"])
background_image = st.file_uploader("Upload Background Image", type=["jpg", "jpeg", "png"])
audio_file = st.file_uploader("Upload Audio File", type=["mp3"])

output_filename = st.text_input("Enter Output Video Filename", "output_video.mp4")

if st.button("Generate Video"):
    if vtt_file and background_image and audio_file:
        with open("uploaded_subtitles.vtt", "wb") as f:
            f.write(vtt_file.read())
        with open("uploaded_background.jpg", "wb") as f:
            f.write(background_image.read())
        with open("uploaded_audio.mp3", "wb") as f:
            f.write(audio_file.read())

        try:
            burn_subtitles_with_background("uploaded_subtitles.vtt", "uploaded_background.jpg", "uploaded_audio.mp3", output_filename)
            st.success(f"Video successfully generated: {output_filename}")
            with open(output_filename, "rb") as video_file:
                st.download_button(
                    label="Download Video",
                    data=video_file,
                    file_name=output_filename,
                    mime="video/mp4"
                )
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please upload all required files.")
