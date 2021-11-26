import os
import json
import requests
import sys, getopt
import moviepy.editor as mpy

def process_audio(audio_link):
    url = requests.get(audio_link)
    with open('temp.mp3', 'wb') as a:
        a.write(url.content)
        if audio_link == "http://www.everyayah.com/data/AbdulSamad_64kbps_QuranExplorer.Com/001001.mp3":
            audio_obj = mpy.AudioFileClip('temp.mp3').subclip(0,6)
        else:
            audio_obj = mpy.AudioFileClip('temp.mp3')
        os.remove('temp.mp3')
    return audio_obj

def process_image(image_link, audio_obj, audio_cum_duration):
    image_obj = (mpy.ImageClip(image_link)
                .set_start(audio_cum_duration)
                .set_duration(audio_obj.duration)
                .resize(height=150, width=150) # if you need to resize...
                .margin(right=8, top=8, bottom=200,opacity=0)
                .set_pos(("center")))
    return image_obj      

def split_text(text):
    words = text.split()
    first_half = round(len(words)/2)
    text_1 = ' '.join(words[:first_half])
    text_2 = ' '.join(words[first_half:])
    full_text = '\n'.join([text_1, text_2])
    return full_text

def process_text(full_text, audio_obj, audio_cum_duration):
    text_obj = (mpy.TextClip(full_text, fontsize=33, font='Arial-Bold', color='black', kerning=2, stroke_color='black', stroke_width=0.6)
               .set_start(audio_cum_duration)
               .set_duration(audio_obj.duration)
               .set_pos(("center"))
               .margin(bottom=20, left=8, right=8, top=8,opacity=0))
    return text_obj

def process_video(video_link, video_source, count):
    # Check the video source 
    file_name = video_link

    if video_source == 'url':
        url = requests.get(video_link)
        file_name = 'temp_'+str(count)+'.mp4'
        
        with open(file_name, 'wb') as a:
            a.write(url.content)
            video_obj = mpy.VideoFileClip(file_name)

    elif video_source == 'local':
        video_obj = mpy.VideoFileClip(file_name)
    else:
        raise ValueError('Invalid video source')

    return video_obj, file_name

def video_processing_automation(inputfile, outputfile, video_source):
    # Opening JSON file
    f = open(inputfile)
    
    # returns JSON object as
    # a dictionary
    data = json.load(f)

    # Buffers for clips to be concatenated 
    audio_clips = []
    image_clips = []
    text_clips = []
    video_clips = []
    video_clips_sizes = []
    videos_count = 0
    files_names = []

    # Save the cummulative durations of the audio clips and video clips
    audio_cum_duration = 0

    # Iterating through the json content field
    for content in data['content']:

        # Process Audio and save the duration
        audio_obj = process_audio(content['audio'])

        # Add to the audio clips
        audio_clips.append(audio_obj)
        
        
        # Process Image and set it's duration
        image_obj = process_image(content['image'], audio_obj, audio_cum_duration)

        # Add to the image clips
        image_clips.append(image_obj)

        
        # Process Text and set it's duration
        full_text = content['text']
        text_chars_limit = 60
        if len(full_text) > text_chars_limit:
            full_text = split_text(full_text)
        text_obj = process_text(full_text, audio_obj, audio_cum_duration)

        # Add to the text clips
        text_clips.append(text_obj)

        
        # Update the cummulative audio duration
        audio_cum_duration += audio_obj.duration

    
    # Iterating through the json background field
    for background in data['background']:
        videos_count+=1

        # Process video based on the video source
        video_obj, file_name = process_video(background['video'], video_source, videos_count)

        # Save the files_names to remove it from the system later
        files_names.append(file_name)

        # Add to the video clips
        video_clips.append(video_obj)

        # Add the video obj size to get the min size to unify it for the whole video
        video_clips_sizes.append(video_obj.size)


    # Put the full background videos on one scale
    video_size = max(video_clips_sizes)

    # Resize each video to that size
    for index, video in enumerate(video_clips):
        video_clips[index] = video.resize(video_size)

    # Concatenate all of the video clips
    full_video = mpy.concatenate_videoclips(video_clips)
    full_video_duration = full_video.duration


    # Move over the clips index circulary
    counter = 0

    # Loop only over the original clips not the copied ones
    video_clips_len = len(video_clips) 
    
    # Keep concatenating clips more and more until we get higher video duration
    while(full_video_duration < audio_cum_duration):

        # get the index of the next clip to append
        video_clip_index = counter % video_clips_len
        video_clips.append(video_clips[video_clip_index])

        # Concatenate the new clips list and check the duration
        full_video = mpy.concatenate_videoclips(video_clips)
        full_video_duration = full_video.duration

        counter+=1


    # Concatenate the audio clips
    full_audio = mpy.concatenate_audioclips(audio_clips)

    # Get the final video with added audio
    full_video = (full_video
                .set_duration(audio_cum_duration)
                .set_audio(full_audio))

    # Composite the text clips and the image clips into the full video
    final_video = mpy.CompositeVideoClip([full_video, *text_clips, *image_clips], size=full_video.size)

    # Write the final video to the desk
    final_video.write_videofile(outputfile)

    # Clean enviroment
    if video_source == 'url':
        for file_name in files_names:
            os.remove(file_name)
    f.close()

def main(argv):
    # Envairoment variable
    inputfile = 'input_url.json'
    outputfile = 'processed_video_2.mp4'
    video_source = 'url'

    try:
      opts, args = getopt.getopt(argv,"hi:o:v:",["ifile=","ofile=","vsource"])
    except getopt.GetoptError:
      print ('video_processing_script.py -i <inputfile> -o <outputfile> -v <videosource>')
      sys.exit(2)

    for opt, arg in opts:
      if opt == '-h':
         print ('video_processing_script.py -i <inputfile> -o <outputfile> -v <videosource>')
         sys.exit()
      elif opt in ("-i", "--ifile"):
         inputfile = arg
      elif opt in ("-o", "--ofile"):
         outputfile = arg
      elif opt in ("-v", "--vsource"):
         video_source = arg

    print('############### Script Paramters ###############')
    print('========> Input file is : ', inputfile)
    print('========> Output file is : ', outputfile)
    print('========> Video source is : ', video_source)
    print("#################################################")
    print("========> Please Wait..........")

    video_processing_automation(inputfile, outputfile, video_source)

if __name__ == "__main__":
    main(sys.argv[1:])