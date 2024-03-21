import yt_dlp

def get_playlist_videos(playlist_url):
    ydl_opts = {
        #'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
        'force_playlist': True,
        'skip_download': True,
        'geo_bypass': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)
        videos = playlist_info['entries']

        if videos:
            video_links = [video['title'] for video in videos]
            return video_links
        else:
            print("No videos found in the playlist.")
            return []
playlist_link = 'https://www.youtube.com/playlist?list=PLMKeTvsD7KjQRJpy55-sYsl2ZZkd7ywcq'

if __name__ == "__main__":
    playlist_url = input("Enter the YouTube playlist URL: ")
    video_links = get_playlist_videos(playlist_url)
    print("Video Links:")
    for link in video_links:
        print(link)
    print(len(video_links))