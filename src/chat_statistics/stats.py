import json
from pathlib import Path
from typing import Union

import arabic_reshaper
from bidi.algorithm import get_display
from hazm import Normalizer, word_tokenize
from src.data import DATA_DIR
from wordcloud import WordCloud
from loguru import logger


class chatstatistics:
    """
    Generates chat statistics from a telegram chat json file
    
    """

    def __init__(self , chat_json : Union[str , Path]):

        """
        :param chat_json: path to telegram export json file

        """
        #load chat data
        logger.info(f"loading chat data from {chat_json}")
        with open(chat_json) as f:
            self.chat_data = json.load(f)
            self.normalizer = Normalizer()
            # load stopword
            logger.info(f"loading stopwords from {DATA_DIR / 'stopwords.txt'}")
            stop_words = open(DATA_DIR /'stop_words.txt').readlines()
            stop_words = list(map(str.strip , stop_words))
            self.stop_words = list(map(self.normalizer.normalize , stop_words))

            #generate word cloud 

    def generate_word_cloud (self ,
     output_dir : Union[str , Path] ,
      width : int = 800 , height : int = 600 ,
       max_font_size : int = 250):
        """
        Generates a word cloud from the chat data
        :param output_dir: path to output directory for word cloud image and top user statistics.

        """
        logger.info(f"Loading text content")
        text_content = ''
        for msg in self.chat_data['messages']:
            if type(msg['text']) is str :
                tokens = word_tokenize(msg['text'])
                tokens = list(filter(lambda item : item not in self.stop_words , tokens))
                text_content += f" {' '.join(tokens)}"

         # normalize , reshape for finall wordcloud

        text_content = self.normalizer.normalize(text_content)
        logger.info(f"using arabic_reshaper ...")
        text_content = arabic_reshaper.reshape(text_content)
        #text_content = get_display(text_content)   when ran it , the text will have problem !!
        

        logger.info(f"Generating word cloud ...")
        wordcloud = WordCloud(width = 1200 ,
        height = 800 ,
        font_path = str(DATA_DIR /'./BHoma.ttf'),
        max_font_size= 250 ,
        background_color = 'black').generate(text_content)


        logger.info(f"saving word cloud to {output_dir}")
        wordcloud.to_file(str(Path(output_dir) / 'wordcloud.png'))


if __name__=="__main__" :
    chat_stats = chatstatistics(chat_json = DATA_DIR / 'online.json')
    chat_stats.generate_word_cloud(output_dir = DATA_DIR)
    print("everythings is Done bro!")
