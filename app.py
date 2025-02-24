import streamlit as st
import subprocess
import os

# Sidebar settings for subtitle style
st.sidebar.header("🎨 Subtitle Styling Settings")
font_name = st.sidebar.text_input("Font Name", "Nunito")
font_size = st.sidebar.slider("Font Size", 20, 100, 62)
primary_color = st.sidebar.color_picker("Primary Colour", "#FFFFFF")
secondary_color = st.sidebar.color_picker("Secondary Colour", "#0000FF")
outline_color = st.sidebar.color_picker("Outline Colour", "#000000")
back_color = st.sidebar.color_picker("Background Colour", "#80000000")
bold = st.sidebar.checkbox("Bold", True)
italic = st.sidebar.checkbox("Italic", False)
alignment = st.sidebar.selectbox("Alignment", ["Bottom Center (2)", "Top Center (8)", "Middle Center (5)"], index=0)

# Convert HEX to ASS format
def hex_to_ass_color(hex_color):
    hex_color = hex_color.lstrip('#')
    return f"&H00{hex_color[4:6]}{hex_color[2:4]}{hex_color[0:2]}"

# Convert VTT to ASS with custom styling
def convert_vtt_to_ass(vtt_path, ass_path):
    ass_template = f"""[Script Info]
Title: Styled Subtitles
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{hex_to_ass_color(primary_color)},{hex_to_ass_color(secondary_color)},{hex_to_ass_color(outline_color)},{hex_to_ass_color(back_color)},{-1 if bold else 0},{1 if italic else 0},0,0,100,100,0,0,1,3,2,{alignment[0]},{10},{10},{490},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def convert_time(vtt_time):
        h, m, s = vtt_time.split(":")
        s, ms = s.split(".")
        ms = ms[:2]  # Keep two decimal places
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

    st.success("✅ Subtitle style applied and converted to .ASS format!")


# Upload Files
st.title("🎬 Subtitle Video Generator")
vtt_file = st.file_uploader("Upload Subtitle File (.vtt)", type=["vtt"])
background_image = st.file_uploader("Upload Background Image", type=["jpg", "jpeg", "png"])
audio_file = st.file_uploader("Upload Audio File (.mp3)", type=["mp3"])

# Output filename input
output_filename = st.text_input("Output Video Filename", "final_video.mp4")

if st.button("Generate Video 🎥"):
    if vtt_file and background_image and audio_file:
        with open("input_subtitles.vtt", "wb") as f:
            f.write(vtt_file.read())
        with open("background.jpg", "wb") as f:
            f.write(background_image.read())
        with open("audio.mp3", "wb") as f:
            f.write(audio_file.read())

        # Convert and process video
        ass_file = "converted_subtitles.ass"
        convert_vtt_to_ass("input_subtitles.vtt", ass_file)

        temp_bg_video = "temp_background.mp4"
        temp_final_video = "temp_final.mp4"

        try:
            subprocess.run([
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", "background.jpg",
                "-c:v", "libx264",
                "-t", "3:14",
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                "-pix_fmt", "yuv420p",
                temp_bg_video
            ], check=True)

            subprocess.run([
                "ffmpeg", "-y",
                "-i", temp_bg_video,
                "-vf", f"ass={ass_file}",
                "-c:v", "libx264",
                "-preset", "slow",
                "-crf", "18",
                temp_final_video
            ], check=True)

            subprocess.run([
                "ffmpeg", "-y",
                "-i", temp_final_video,
                "-i", "audio.mp3",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                output_filename
            ], check=True)

            st.success(f"✅ Successfully created the video: {output_filename}")
            with open(output_filename, "rb") as file:
                st.download_button("⬇️ Download Video", file, output_filename)

        except subprocess.CalledProcessError as e:
            st.error(f"Error: {e}")
    else:
        st.error("❌ Please upload all required files.")
