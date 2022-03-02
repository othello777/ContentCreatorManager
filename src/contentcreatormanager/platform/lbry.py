'''
Created on Feb 24, 2022

@author: tiff
'''
import contentcreatormanager.platform.platform
import contentcreatormanager.media.video.lbry
import contentcreatormanager.media.post.lbry
import requests

class LBRY(contentcreatormanager.platform.platform.Platform):
    '''
    classdocs
    '''
    #URL used to make LBRY API calls
    API_URL = "http://localhost:5279"

    def __get_channel(self):
        """Private method to make api call to get channel info based on claim_id (which is the id property) and return the results"""
        params = {
            'claim_id':self.id
        }
        result = requests.post(LBRY.API_URL, json={"method": "channel_list", "params": params}).json()
        
        #check if API call returned an error if so throw an exception
        if self.check_request_for_error(result):
            #more detailed exception could probably be made to use here
            raise Exception()
        return result
    
    def __add_channel_videos(self):
        """Private method to grab all videos for the channel via api and then use that data to create LBRYVideo objects and add them to media_objects list property"""
        #channel's claim_id is self.id ordering results by name
        params = {
            "channel_id": [self.id],
            "order_by":'name'
        }
        
        #grab first page of data for api call to get all claims assosiated with lbry channel
        intial_result = requests.post(LBRY.API_URL, json={"method": "claim_list", "params": params}).json()
        
        #check if API call returned an error if so throw an exception
        if self.check_request_for_error(intial_result):
            #more detailed exception could probably be made to use here
            raise Exception()
        
        #stores num of pages and items total returned
        page_amount = intial_result['result']['total_pages']
        item_amount = intial_result['result']['total_items']
        
        self.logger.info(f"Found {item_amount} claims on channel {self.id} with {page_amount} page(s) of data")
        
        pages = []
        claims = []
        
        self.logger.info("adding initial request as 1st page of data")
        pages.append(intial_result['result']['items'])
        
        # if there is more than 1 page of data grab the rest
        if page_amount > 1:
            for x in range(page_amount-1):
                params = {
                    "page":x+2, 
                    "channel_id": [self.id],
                    "order_by":'name'      
                }
                self.logger.info(f"getting page {x+2} of data and adding it")
                current_result = requests.post(LBRY.API_URL, json={"method": "claim_list", "params": params}).json()
                pages.append(current_result['result']['items'])
        
        #loops through to get all the claims that are of type video and adds them to claims list    
        page = 0
        x = 0
        for p in pages:
            page += 1
            for i in p:
                x += 1
                if i['value']['stream_type'] == 'video':
                    self.logger.info(f"Adding claim with claim_id {i['claim_id']} and name {i['name']} from page {page} of the results")
                    claims.append(i)
                else:
                    self.logger.info(f"claim {i['name']} is a {i['value']['stream_type']} not a video.  Not adding it")
        
        #in case there were objects already in the list grab current length
        num_claims_before = len(self.media_objects)
        
        #loops through the claims turns them into lbry video objects and adds them as media to the platform
        for c in claims:
            v = contentcreatormanager.media.video.lbry.LBRYVideo(ID=c['claim_id'], lbry_channel=self, request=c)
            
            self.add_media(v)
        
        #using before and after lengths to determine how many LBRYVideo objects were added to self.media_objects
        num_vids_added = len(self.media_objects) - num_claims_before
        self.logger.info(f"Total of {num_vids_added} LBRY Video Objects added to media_objects list")

    def __init__(self, settings : contentcreatormanager.config.Settings, ID : str, init_videos : bool = False):
        '''
        Constructor takes a Settings object.  ID string required (claim_id of the channel to be used).  Set init_videos flag to True to grab all video data from LBRY on creation of LBRY Platform Object.
        '''
        #Call the constructor of the super class to set a few things
        super(LBRY, self).__init__(settings=settings, ID=ID)
        
        #Set appropriate logger for the object
        self.logger = self.settings.LBRY_logger
        self.logger.info("Initializing Platform Object as LBRY Platform object")
        
        #storing result of an api call to get LBRY channel data based on id to finish initializing the object
        result = self.__get_channel()
        
        self.logger.info("Setting address, bid, name, normalized_name, permanent_url, description, email, title, languages, tags, and thumbnail based on api call results")
        self.address = result['result']['items'][0]['address']
        self.bid = result['result']['items'][0]['amount']
        self.name = result['result']['items'][0]['name']
        self.normalized_name = result['result']['items'][0]['normalized_name']
        self.permanent_url = result['result']['items'][0]['permanent_url']
        self.description = result['result']['items'][0]['value']['description']
        self.email = result['result']['items'][0]['value']['email']
        self.title = result['result']['items'][0]['value']['title']
        
        #Some fields are not required for a channel to have and will be missing from the results requiring this filtering to prevent throwing an error
        if 'languages' in result['result']['items'][0]['value']:
            self.languages = result['result']['items'][0]['value']['languages']
        else:
            self.languages = ['en']
        if 'tags' in result['result']['items'][0]['value']:
            self.tags = result['result']['items'][0]['value']['tags']
        else:
            self.tags = []
        if 'thumbnail' in result['result']['items'][0]['value']:    
            self.thumbnail = result['result']['items'][0]['value']['thumbnail']
        else:
            self.thumbnail = None
            
        #If the init_videos flag is set on object creation will run appropriate methods to grab all Videos from the channel and add them to self.media_objects as LBRYVideo Objects
        if init_videos:
            self.logger.info("init_videos set to true grabbing video data and adding to media_objects")
            self.__add_channel_videos()
            
        self.logger.info("LBRY Platform object initialized")
       
    def check_request_for_error(self, request):
        """Method that will check if the result of the LBRY API call provided returned an error or not and if it did will log some errors and return True otherwise it will return False"""
        if 'error' in request:
            self.logger.error("API call returned an error:")
            self.logger.error(f"Error Code: {request['error']['code']}")
            try:
                self.logger.error(f"Error Type: {request['error']['data']['name']}")
            except:
                pass
            self.logger.error(f"Error Message: {request['error']['message']}")
            return True
        return False
    
    def add_video(self, vid : contentcreatormanager.media.video.lbry.LBRYVideo):
        """Method to add a LBRY Video Object to the media_objects list property"""
        self.add_media(vid)
     
    def add_video_with_name(self, name : str, file_name : str, update_from_web : bool = True, upload : bool = False, title : str = '', description : str = '', tags : list = [], bid : str = '0.001'):
        """
        Method to add a LBRY Video Object to the media_objects list property.  This uses the name provided to lookup other details about the video to add if the update_from_web flag 
        is set to True which is the default.  If the upload flag is set to True (default is False) the video will be uploaded after the object is created. upload and update_from_web can not both be True.
        """
        #Makes sure both update from_web and upoad are not both set
        if update_from_web and upload:
            self.logger.error("Either update from web or upload to it not both :P")
            return None
        
        #Create generic LBRY Video Object
        vid = contentcreatormanager.media.video.lbry.LBRYVideo(settings=self.settings, lbry_channel=self, file_name=file_name)
        #Set some properties based on inputs to the method
        vid.name = name
        vid.tags = tags
        vid.title = title
        vid.description = description
        vid.bid = bid
        
        #If update from web is set then use the name to search and update the object properties
        if update_from_web:
            vid.update_local(use_name=True)
        #If upload is set attempt to upload the vid to lbry now
        elif upload:
            if title == '' or description == '':
                self.logger.error("Title and Description Required for new upload.  No upload made")
            else:
                vid.upload()
        #Call add_media from base class and provide it the LBRY Video Object
        self.add_video(vid)
        
    def make_post(self, title : str, body : str, tags : list = [], languages : list = ['en'], bid : str = "0.001", thumbnail_url : str = ''):
        post = contentcreatormanager.media.post.lbry.LBRYTextPost(lbry_channel=self, title=title, body=body, name=title, tags=tags, bid=bid, thumbnail_url=thumbnail_url, languages=languages)
        
        post.upload()
        
        self.add_media(post)
        
        return post
    
    def api_get(self, uri : str, download_directory : str):
        """
        Method to make a get call to the LBRY API
        Example Call: 
        Example Return: 
        """
        
        parameters = dict(
            uri=uri,
            download_directory=download_directory
        )
        
        result = requests.post(LBRY.API_URL, json={"method": "get", "params": parameters}).json()
        
        self.logger.info(f"get call with parameters {parameters} made to the LBRY API")
        
        return result
    
    def api_channel_list(self, claim_id : list = [], page : int = 0, name : str = '', page_size : int = 20, resolve : bool = False):
        """
        Method to make a channel_list call to the LBRY API
        Example Call: 
        Example Return: 
        """
        
        parameters = dict(
            claim_id=claim_id,
            resolve=resolve,
            page_size=page_size
        )
        
        if not (page == 0 or page is None):
            parameters['page'] = page
            
        if not (name == '' or name is None):
            parameters['name'] = name

        
        result = requests.post(LBRY.API_URL, json={"method": "channel_list", "params": parameters}).json()
        
        self.logger.info(f"channel_list call with parameters {parameters} made to the LBRY API")
        
        return result
    
    def api_channel_create(self, name : str, bid : float, title : str, description : str, email : str, website_url : str, featured : list, tags : list, languages : list, thumbnail_url : str, cover_url : str):
        """
        Method to make a channel_create call to the LBRY API
        Example Call: 
        Example Return: 
        """
        
        parameters = dict(
            name=name,
            bid=bid,
            title=title,
            description=description,
            email=email,
            website_url=website_url,
            featured=featured,
            tags=tags,
            languages=languages,
            thumbnail_url=thumbnail_url,
            cover_url=cover_url 
        )
        

        
        result = requests.post(LBRY.API_URL, json={"method": "channel_create", "params": parameters}).json()
        
        self.logger.info(f"channel_create call with parameters {parameters} made to the LBRY API")
        
        return result
    
    def api_channel_abandon(self, claim_id : str):
        """
        Method to make a channel_abandon call to the LBRY API
        Example Call: 
        Example Return: 
        """
        
        parameters = dict(
            claim_id=claim_id
        )

        result = requests.post(LBRY.API_URL, json={"method": "channel_abandon", "params": parameters}).json()
        
        self.logger.info(f"channel_abandon call with parameters {parameters} made to the LBRY API")
        
        return result
    
    def api_channel_update(self, claim_id : str, bid : float, title : str, description : str, email : str, 
                           website_url : str, cover_url : str, featured : list, tags : list, languages : list, 
                           thumbnail_url : str, clear_tags : bool = True, clear_languages : bool = True, 
                           replace : bool = True):
        """
        Method to make a channel_update call to the LBRY API
        Example Call: 
        Example Return: 
        """
        
        parameters = dict(
            claim_id=claim_id,
            bid=bid,
            title=title,
            description=description,
            email=email,
            website_url=website_url,
            featured=featured,
            tags=tags,
            clear_tags=clear_tags,
            clear_languages=clear_languages,
            thumbnail_url=thumbnail_url,
            languages=languages,
            cover_url=cover_url,
            replace=replace
        )
        
        result = requests.post(LBRY.API_URL, json={"method": "channel_update", "params": parameters}).json()
        
        self.logger.info(f"channel_update call with parameters {parameters} made to the LBRY API")
        
        return result
    
    def api_file_save(self, download_directory : str, claim_id : str):
        """
        Method to make a file_save call to the LBRY API
        Example Call: 
        Example Return: 
        """
        
        parameters = dict(
            download_directory=download_directory,
            claim_id=claim_id
        )
        
        result = requests.post(LBRY.API_URL, json={"method": "file_save", "params": parameters}).json()
        
        self.logger.info(f"file_save call with parameters {parameters} made to the LBRY API")
        
        return result
    
    def api_stream_abandon(self, claim_id : str):
        """
        Method to make a stream_abandon call to the LBRY API
        Example Call: 
        Example Return: 
        """
        
        parameters = dict(
            claim_id=claim_id
        )
        
        result = requests.post(LBRY.API_URL, json={"method": "stream_abandon", "params": parameters}).json()
        
        self.logger.info(f"stream_abandon call with parameters {parameters} made to the LBRY API")
        
        return result
    
    def api_stream_create(self, name : str, bid : float, file_path : str, title : str, description: str, tags : list, languages : list, channel_id : str):
        """
        Method to make a stream_create call to the LBRY API
        Example Call: 
        Example Return: 
        """
        
        parameters = dict(
            name=name,
            bid=bid,
            file_path=file_path,
            description=description,
            title=title,
            tags=tags,
            languages=languages,
            channel_id=channel_id
        )
        
        result = requests.post(LBRY.API_URL, json={"method": "stream_create", "params": parameters}).json()
        
        self.logger.info(f"stream_create call with parameters {parameters} made to the LBRY API")
        
        return result
    
    def api_stream_update(self, claim_id : str, bid : float, title : str, description : str, tags : list, 
                          languages : list, channel_id : str, clear_languages : bool = True, 
                          clear_tags : bool = True, replace : bool = True):
        """
        Method to make a stream_update call to the LBRY API
        Example Call: 
        Example Return: 
        """
        
        parameters = dict(
            claim_id=claim_id,
            bid=bid,
            title=title,
            description=description,
            tags=tags,
            languages=languages,
            channel_id=channel_id,
            replace=replace,
            clear_tags=clear_tags,
            clear_languages=clear_languages
        )
        
        result = requests.post(LBRY.API_URL, json={"method": "stream_update", "params": parameters}).json()
        
        self.logger.info(f"stream_update call with parameters {parameters} made to the LBRY API")
        
        return result
    
    def api_claim_list(self, claim_type : list, claim_id, list, channel_id: list, name : list, 
                       account_id : str, order_by : str = '', page : int = 0, resolve : bool = True, page_size: int = 20):
        """
        Method to make a claim_list call to the LBRY API
        Example Call: 
        Example Return: 
        """
        
    
        parameters = dict(
            claim_type=claim_type,
            claim_id=claim_id,
            channel_id=channel_id,
            name=name,
            page_size=page_size,
            resolve=resolve,
        )
        
        if not (account_id == '' or account_id is None):
            parameters['account_id']=account_id
        
        if not (page == 0 or page is None):
            parameters['page']=page
        
        if not (order_by == '' or order_by is None):
            parameters['order_by']=order_by
        
        
        result = requests.post(LBRY.API_URL, json={"method": "claim_list", "params": parameters}).json()
        
        self.logger.info(f"claim_list call with parameters {parameters} made to the LBRY API")
        
        return result