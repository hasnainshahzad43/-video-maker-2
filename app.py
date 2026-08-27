import os
import asyncio
import re
import time
import requests
import streamlit as st
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

# Streamlit Configuration
st.set_page_config(page_title="StudioAI Final", page_icon="🎬", layout="centered")

# Custom UI Styling
st.markdown("""
    <style>
    body { background-color: #0b0c10; }
    h1 { text-align: center; color: #66fcf1; font-family: 'Arial Black', sans-serif; font-size: 32px; }
    div.stButton > button:first-child { background: linear-gradient(135deg, #1f4068 0%, #162447 100%); color: #66fcf1; font-weight: bold; height: 55px; border-radius: 8px; border: 2px solid #45f3ff; font-size: 18px; box-shadow: 0 0 15px rgba(69,243,255,0.4); }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>🎬 StudioAI: Premium Video Engine</h1>", unsafe_allow_html=True)

st.subheader("1. Project Setup")
col1, col2 = st.columns(2)
with col1:
    ratio_choice = st.selectbox("Choose Format:", ["📱 Vertical Shorts / Reels (9:16)", "📺 Horizontal YouTube (16:9)"])
    v_width, v_height = (720, 1280) if "📱" in ratio_choice else (1280, 720)
with col2:
    voice_options = {
        "🎙️ Deep Mystery Male (Brian - UK)": "en-GB-BrianNeural",
        "🎙️ Cinematic Dark Male (Andrew - USA)": "en-US-AndrewNeural"
    }
    selected_voice = voice_options[st.selectbox("Select Deep Voice:", list(voice_options.keys()))]

st.subheader("2. Premium Effects & Mood")
mood_choice = st.selectbox("Visual Art Style:", ["🩸 True Crime Realism", "🌌 Dark Mystery & Cosmos"])
mood_prompts = {
    "🩸 True Crime Realism": "highly detailed gritty true crime documentary photography dark shadows dramatic lighting 4k resolution cinematic raw vignette",
    "🌌 Dark Mystery & Cosmos": "surreal cosmic mystery deep dark space cinematic nebula high contrast realistic photography 4k"
}

user_script = st.text_area("Enter Your Script (Each line is a unique automated premium scene):", 
                           value="The detective entered the abandoned asylum.\nInside, the room hidden a dark secret.", height=180)

lines = [line.strip() for line in user_script.split('\n') if line.strip()]

async def generate_audio(text, voice, output_path):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if st.button("Generate Premium Video 🚀", use_container_width=True):
    if not lines:
        st.error("Please write your script first!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        video_clips = []
        total_scenes = len(lines)
        
        for i, line in enumerate(lines):
            status_text.markdown(f"🎭 **Rendering Premium Scene {i+1}/{total_scenes}...**")
            audio_path = f"voice_{i}.mp3"
            
            # Safe Audio Generation with Retries
            audio_success = False
            for attempt in range(3):
                try:
                    asyncio.run(generate_audio(line, selected_voice, audio_path))
                    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                        audio_success = True
                        break
                except Exception as tts_err:
                    time.sleep(2)  # Wait before retrying
            
            # If Audio Fails, skip to avoid app crash
            if not audio_success:
                st.warning(f"⚠️ Scene {i+1} ka audio skip ho gaya server load ki wajah se.")
                continue
                
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            clean_prompt = re.sub(r'[^a-zA-Z0-9\s]', '', line)
            final_prompt = f"{mood_prompts[mood_choice]} {clean_prompt}"
            
            encoded_prompt = requests.utils.quote(final_prompt)
            image_url = f"https://pollinations.ai{encoded_prompt}?width={v_width}&height={v_height}&enhance=true&seed={i}"
            image_path = f"image_{i}.jpg"
            
            try:
                img_data = requests.get(image_url, timeout=25).content
                with open(image_path, 'wb') as handler: 
                    handler.write(img_data)
                
                base_clip = ImageClip(image_path).with_duration(duration)
                img_clip = base_clip.resized(lambda t: 1 + 0.06 * t)
            except Exception as img_err:
                from moviepy import ColorClip
                img_clip = ColorClip(size=(v_width, v_height), color=(10, 12, 18)).with_duration(duration)
            
            scene_clip = img_clip.with_audio(audio_clip)
            video_clips.append(scene_clip)
            progress_bar.progress(int((i + 1) / total_scenes * 100))
            
            # Rate limiting delay to keep Microsoft Edge TTS Server happy
            time.sleep(2)
            
        if not video_clips:
            st.error("❌ Koi bhi scene generate nahi ho saka. Dubara koshish karein.")
        else:
            status_text.markdown("🎥 **Compiling final video export...**")
            try:
                final_video = concatenate_videoclips(video_clips, method="compose")
                output_video = "premium_viral_output.mp4"
                final_video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac")
                
                final_video.close()
                for i in range(len(lines)):
                    try:
                        os.remove(f"voice_{i}.mp3")
                        os.remove(f"image_{i}.jpg")
                    except: 
                        pass
                
                status_text.empty()
                progress_bar.empty()
                st.success("🎉 Premium Video Generated!")
                st.video(output_video)
                
                with open(output_video, "rb") as file:
                    st.download_button("📥 Download Video to Gallery", data=file, file_name="premium_ai_documentary.mp4", mime="video/mp4", use_container_width=True)
            except Exception as e:
                st.error(f"Error during video composition: {e}")
