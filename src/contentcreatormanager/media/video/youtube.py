"""
Created on Feb 24, 2022

@author: tiff
"""
import contentcreatormanager.media.video.video as media_vid
import pytube
import os.path
import time
import requests

class YouTubeVideo(media_vid.Video):
    """
    classdocs
    """
    
    BASE_URL = "https://www.youtube.com/watch?v="
    
    MAX_RETRIES = 25
    
    def __aud_dl(self):
        py = self.pytube_obj.streams.filter(only_audio=True)
        return py.order_by('abr').desc().first().download(filename_prefix="audio_")
    
    def __vid_dl(self):
        """
        private method to run pytube vid download
        """
        py = self.pytube_obj.streams.order_by('resolution')
        return py.desc().first().download(filename_prefix="video_")
    
    def __pytube_download_video(self):
        """
        Private Method to download the video portion of 
        this YouTube Video Object
        """
        m=f"Attempting to download video portion of {self.title}"
        self.logger.info(m)
        video_file = None
        finished = False
        tries = 0
       
        #pytube has weird transient failures that you just keep trying 
        # and things work so this loop does that to a point for the video
        while not finished and tries < YouTubeVideo.MAX_RETRIES + 2:
            try:
                video_file = self.__vid_dl()
                finished = True
            except KeyError as e:
                if e.args[0] == 'content-length':
                    self.logger.error("pytube content-length bug skipping")
                    return 'content-length-error'
            except Exception as e:
                if tries > YouTubeVideo.MAX_RETRIES:
                    m="Too many failed download attempts raising new exception"
                    self.logger.error(m)
                    raise Exception()
                self.logger.error(f"got error:\n{e}\nGoing to try again")
                tries += 1
                m=f"{tries} tries of a possible {YouTubeVideo.MAX_RETRIES}"
                self.logger.info(m)
                finished = False
        
    
        self.logger.info(f"Downloaded video for {self.title}")
        return video_file
        
        
    def __pytube_download_audio(self):
        """
        Private Method to download the audio portion
        of the YouTube Video Object
        """
        m=f"Attempting to download audio portion of {self.title}"
        self.logger.info(m)
        
        # pytube has weird transient failures that you just keep trying 
        # and things work so this loop does that to a point for the audio
        finished = False
        tries = 0
        while not finished and tries < YouTubeVideo.MAX_RETRIES + 2:
            try:
                audio_file = self.__aud_dl()
                finished = True
            except Exception as e:
                if tries > YouTubeVideo.MAX_RETRIES:
                    m="Too many failed download attempts raising new exception"
                    self.logger.error(m)
                    raise Exception()
                self.logger.error(f"got error:\n{e}\nGoing to try again")
                tries += 1
                m=f"{tries} tries of a possible {YouTubeVideo.MAX_RETRIES}"
                self.logger.info(m)
                finished = False
        
        self.logger.info(f"Downloaded audio for {self.title}")
        return audio_file
    
    def __pytube_download(self, overwrite : bool = False):
        """
        Private Method to download a video from YouTube using pytube. 
        Optional parameter overwrite is a bool that defaults to False.
        If set to true an existing file will be overwritten.
        """
        file_name = os.path.basename(self.file)
        file_path = self.file
        self.logger.info(f"Downloading {file_name}")
        
        if os.path.isfile(file_path):
            self.logger.info(f"File {file_name} already exists.")
            if overwrite:
                self.logger.info("Overwrite set removing file re-downloading")
                os.remove(self.file)
            else:
                self.logger.info("Overwrite not set not downloading")
                return
        
        video_file = self.__pytube_download_video()
        
        if video_file == 'content-length-error':
            self.logger.error("Can not download this video")
            return 'content-length-error'
        
        audio_file = self.__pytube_download_audio()
        
        self.combine_audio_and_video_files(video_file, audio_file)
    
    def __url(self):
        """
        Private Method to get YouTube URL
        """
        url = f"{YouTubeVideo.BASE_URL}{self.id}"
        return url
    
    def __get_pytube(self, use_oauth=True):
        """
        Private method that returns the pytube.YouTube
        object for this YouTubeVideo
        """
        url = self.__url()
        return pytube.YouTube(url, use_oauth=use_oauth)
    
    def __init__(self, channel, ID : str = None, favorite_count : str ='0', 
                 comment_count : str ='0', dislike_count : str ='0', 
                 like_count : str ='0', view_count : str ='0', 
                 self_declared_made_for_kids : bool =False,
                 made_for_kids : bool =False,public_stats_viewable:bool =True,
                 embeddable : bool =True, lic : str ='youtube',
                 privacy_status : str ="public",
                 upload_status : str ='notUploaded', 
                 has_custom_thumbnail : bool =False, 
                 content_rating : dict ={}, licensed_content : bool =False, 
                 default_audio_language : str ='en-US', published_at=None,
                 channel_id=None, title='', description=None,
                 file_name : str = '', update_from_web : bool = False,
                 thumbnails : dict ={}, channel_title=None, tags : list =[],
                 category_id : int =22, live_broadcast_content=None,
                 new_video : bool =False):
        """
        Constructor takes a YouTube Platform object as its only parameter 
        without a default value.  All properties can be set on creation of
        the Object.  If the object is a new video not yet on YouTube set 
        the new_video flag to True, and if you want the object to be updated
        based on a web lookup with the ID set the update_local flag to True.
        """
        super(YouTubeVideo, self).__init__(platform=channel,
                                           ID=ID,file_name=file_name)
        self.logger = self.settings.YouTube_logger
        
        self.logger.info("Initializing Video Object as a YouTube Video Object")
        
        self.channel = channel
        
        self.published_at = published_at
        self.channel_id = channel_id
        self.title = title
        self.description = description
        self.thumbnails = thumbnails
        self.channel_title = channel_title
        self.tags = tags
        self.category_id = category_id
        self.live_broadcast_content = live_broadcast_content
        self.default_audio_language = default_audio_language
        self.default_language = default_audio_language
        self.licensed_content = licensed_content
        self.content_rating = content_rating
        self.has_custom_thumbnail = has_custom_thumbnail
        self.upload_status = upload_status
        self.privacy_status = privacy_status
        self.license = lic
        self.embeddable = embeddable
        self.public_stats_viewable = public_stats_viewable
        self.made_for_kids = made_for_kids
        self.self_declared_made_for_kids = self_declared_made_for_kids
        self.view_count = view_count
        self.like_count = like_count
        self.dislike_count = dislike_count
        self.comment_count = comment_count
        self.favorite_count = favorite_count
        
        if file_name == '':
            file_name = self.title
        
        if new_video:
            m="new_video not attempting to initialize pytube_obj variable"
            self.logger.info(m)
            self.pytube_obj = None
        else:
            m="not new_video.  Attempting to initialize pytube_obj property"
            self.logger.info(m)
            self.pytube_obj = self.__get_pytube()
            if update_from_web:
                m="update_video flag set.  Grabbing Video details from YouTube"
                self.logger.info(m)
                self.update_local()
                self.logger.info("update ran")
                
        
        self.logger.info("YouTube Video Object initialized")
        
    def get_thumb_url(self):
        """
        Returns the url of the video's thumbnail
        """
        return f"https://img.youtube.com/vi/{self.id}/default.jpg"
    
    def is_downloaded(self):
        """
        Checks for downloaded file
        """
        if not self.uploaded:
            if self.is_uploaded():
                self.update_local()
        else:
            self.update_local()       
        result = media_vid.Video.is_downloaded(self)
        return result
    
    def delete_web(self, do_not_download_before_delete : bool = False):
        """
        Method to make the videos.delete API call to youtube and return the
        results.  If the video is not downloaded and you do not want to
        download it before removal from YouTube set the 
        do_not_download_before_delete flag to True
        """
        m=f"Preparing to delete video with ID {self.id} from YouTube"
        self.logger.info(m)
        
        if not self.is_downloaded() and not do_not_download_before_delete:
            m="File for video not found.  Downloading before removal"
            self.logger.warning(m)
            result = self.download()
            if result == 'content-length-error':
                self.logger.error("Download failed with pytube issue not removing")
                return 'content-length-error'
        
        self.logger.info("Making videos.delete api call")
        request = self.channel.service.videos().delete(
            id=self.id
        )
        result = request.execute()
        
        tries_left = YouTubeVideo.MAX_RETRIES
        while self.is_uploaded() and tries_left > 0:
            m=f"Video found on YouTube.  Sleeping a minute and checking again."
            self.logger.warning(m)
            time.sleep(60)
            tries_left -= 1
        
        if self.uploaded:
            m=f"Video still found on YouTube.  Results of the call:\n{result}"
            self.logger.error(m)
        else:
            self.logger.info("Delete successful")
        
        return result

    def update_web(self, force_update : bool = False):
        """
        Method to update Video details on YouTube based on the
        local object's properties.  This makes a videos.update call.  
        This method checks to see if an update is needed by making 
        a videos.list call and comparing the local and web properties 
        before sending the update call.  This is because a videos.list
        API call is one quota unit where as the update is 50.  
        Set force_update to ignore this check.
        """
        if not self.uploaded:
            if not self.is_uploaded():
                m="Video not uploaded.  Can not update its web details"
                self.logger.error(m)
                return
        
        update_snippet = {}
        update_snippet['categoryId']=self.category_id
        update_snippet['defaultLanguage']=self.default_language
        update_snippet['description']=self.description
        update_snippet['tags']=self.tags
        update_snippet['title']=self.title
        update_status = {}
        update_status['embeddable']=self.embeddable
        update_status['license']=self.license
        update_status['privacyStatus']=self.privacy_status
        update_status['publicStatsViewable']=self.public_stats_viewable
        update_status['selfDeclaredMadeForKids']=self.self_declared_made_for_kids
        
        if not force_update:
            current_web_status = self.platform.api_videos_list(ids=self.id,
                                                               snippet=True,
                                                               contentDetails=True,
                                                               statistics=True,
                                                               status=True)
        
            current_web_snippet = current_web_status['snippet']
            current_web_status = current_web_status['status']
        
            need_to_update=False
            
            cond1 = update_snippet == current_web_snippet
            cond2 = update_status == current_web_status
            if not (cond1 and cond2):
                need_to_update = True
            
            if not need_to_update:
                self.logger.info("No need to update returning None")
                return None

        m="Making videos.update call to YouTube API to update Video details"
        self.logger.info(m)
        request = self.channel.service.videos().update(
            part='snippet,status',
            body=dict(
                snippet=update_snippet,
                status=update_status,
                id=self.id
            )
        )
        return request.execute()
    
    def update_local(self, update_file_name : bool = True):
        """
        Method to update the local properties based on the web properties
        """
        if not self.uploaded:
            self.logger.info("uploaded flag not set checking if uploaded")
            if not self.is_uploaded():
                m="Can not update local details from YouTube"
                self.logger.error(m)
                return
        
        self.logger.info(f"Updating Video with id {self.id} from the web")
        
        video = self.platform.api_videos_list(ids=self.id, snippet=True,
                                              contentDetails=True,
                                              statistics=True,
                                              status=True)['items'][0]
        
        if video is None:
            self.logger.error(f"Trying to update local but can not find video")
            return None
        
        if 'tags' not in video['snippet']:
            tags = []
        else:
            tags = video['snippet']['tags']
        if 'description' not in video['snippet']:
            description = ""
        else:
            description = video['snippet']['description']
        if 'selfDeclaredMadeForKids' not in video['status']:
            self_declared_made_for_kids = False
        else:
            s=video['status']['selfDeclaredMadeForKids']
            self_declared_made_for_kids = s
        if 'defaultAudioLanguage' not in video['snippet']:
            default_audio_language = 'en-US'
        else:
            d=video['snippet']['defaultAudioLanguage']
            default_audio_language = d
    
        self.published_at = video['snippet']['publishedAt']
        self.channel_id = video['snippet']['channelId']
        self.title = video['snippet']['title']
        self.description = description
        self.thumbnails = video['snippet']['thumbnails']
        self.channel_title = video['snippet']['channelTitle']
        self.tags = tags
        self.category_id = video['snippet']['categoryId']
        self.live_broadcast_content = video['snippet']['liveBroadcastContent']
        self.default_audio_language = default_audio_language
        self.licensed_content = video['contentDetails']['licensedContent']
        self.content_rating = video['contentDetails']['contentRating']
        self.has_custom_thumbnail = video['contentDetails']['hasCustomThumbnail']
        self.upload_status = video['status']['uploadStatus']
        self.privacy_status = video['status']['privacyStatus']
        self.license = video['status']['license']
        self.embeddable = video['status']['embeddable']
        self.public_stats_viewable = video['status']['publicStatsViewable']
        self.made_for_kids = video['status']['madeForKids']
        self.self_declared_made_for_kids = self_declared_made_for_kids
        self.view_count = video['statistics']['viewCount']
        self.like_count = video['statistics']['likeCount']
        self.dislike_count = video['statistics']['dislikeCount']
        self.comment_count = video['statistics']['commentCount']
        self.favorite_count = video['statistics']['favoriteCount']

        
        if update_file_name:
            print(self.title)
            f=self.get_valid_video_file_name(desired_file_name=self.title)
            file_name = f
            self.file = os.path.join(os.getcwd(), file_name)
        
        self.logger.info("Update from web complete")
        return video
        
    def upload(self):
        """
        Method to upload Video to YouTube
        """
        file = self.file
        privStatus = self.privacy_status
        self.privacy_status = 'private'
        
        if self.uploaded:
            self.logger.warning("Vid is uploaded not running upload again")
            return
        
        if not os.path.isfile(file):
            self.logger.error("Can not find file no upload made")
            return
        
        try:
            self.logger.info(f"Attempting to upload {file}")
            self.__initialize_upload()
        except Exception as e:
            self.logger.error(f"Error during upload:\n{e}")
            return
        
        self.pytube_obj = self.__get_pytube()
        self.update_local()
        
        if self.privacy_status == privStatus:
            self.logger.info("Video Upload Complete")
            return
        
        m=f"Setting privacy status to {privStatus} and running an update"
        self.logger.info(m)
        self.privacy_status = privStatus
        self.update_web()
        
        self.logger.info("Video Upload Complete")
    
    def download(self, overwrite=False):
        """
        Method to download the video from YouTube.
        Set overwrite to True if you want an existing file overwritten
        """
        if not self.uploaded:
            if not self.is_uploaded():
                self.logger.error("Video not uploaded. Can not download it")
                return
        result = self.__pytube_download(overwrite=overwrite)
        
        return result
        
    def is_uploaded(self):
        """
        Method to check if the Video is uploaded to Youtube.
        This should only have a quota cost of 1.  Returns True
        if the video is found on YouTube.  Check is done with
        API so that private users videos will be found and
        checked appropriately.
        """
        #First Try and check without API
        url = self.__url()

        response = requests.get(url)
        if response.status_code == 200:
            if not "Video unavailable" in response.text:
                self.uploaded = True
                return True
        
        result = self.platform.api_videos_list(contentDetails=True,ids=self.id)
        
        if result['pageInfo']['totalResults'] == 0:
            self.uploaded = False
            return False
        else:
            self.uploaded = True
            return True