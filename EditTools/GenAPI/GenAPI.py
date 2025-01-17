class TextGen:
    """ Class for generating content using GPT-4o-mini model from OpenAI API """
    def __init__(self, API_KEY, system_prompt, text):
        self.API_KEY = API_KEY
        self.system_prompt = system_prompt  
        self.text = text  
        
    def generate(self):  
        from openai import OpenAI  
        
        client = OpenAI(api_key=self.API_KEY)  
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  
                messages=[
                    {"role": "system", "content": self.system_prompt},  
                    {"role": "user", "content": self.text}  
                ],
                max_tokens=16384, 
                response_format={ "type": "json_object" }  
            )
            return response
        except Exception as e:
            print(f"Error en el TextGen: {str(e)}")
            raise

class ClientTTS:
    """ Class for generating TTS using OpenAI API """
    def __init__(self, API_KEY, text, voice_type, default_output_dir=None):
        from pathlib import Path

        self.API_KEY = API_KEY
        self.text = text
        self.voice_type = voice_type
        self.default_output_dir = Path(default_output_dir) if default_output_dir else Path(__file__).parent
    
    def generateTTS(self, output_path=None):
        from openai import OpenAI
        from pathlib import Path

        if output_path is None:
            output_path = self.default_output_dir / "speech.mp3"
        else:
            output_path = Path(output_path)

        client = OpenAI(api_key=self.API_KEY)

        try: 
            response = client.audio.speech.create(
                model="tts-1",
                voice=self.voice_type,
                input=self.text,
            )
            response.stream_to_file(output_path)
            
            # Alternativa usando with_streaming_response si stream_to_file falla
            # with open(output_path, 'wb') as f:
            #     for chunk in response.with_streaming_response.iter_bytes():
            #         f.write(chunk)
            return output_path        
        except Exception as e:
            print(f"Error en el ClientTTS: {str(e)}")
            raise
