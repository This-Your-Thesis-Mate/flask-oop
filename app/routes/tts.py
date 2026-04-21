"""
Text-to-Speech routes for converting text chunks to speech
"""
import base64
from flask import Blueprint, request, jsonify, send_file
from app.routes.base_handler import BaseRouteHandler
from app.services.tts_service import tts_service

tts_bp = Blueprint('tts', __name__)


class TTSHandler(BaseRouteHandler):
    """Handler for Text-to-Speech operations"""
    
    @staticmethod
    def convert_module_to_speech(module_id):
        """
        Convert all chunks from a module to MP3 files
        
        Path parameter:
            - module_id: Module ID to convert
        
        JSON body (optional):
            - language: Language code (default 'id' for Indonesian)
            - slow: Speak slowly (default False)
            - output_dir: Directory to save MP3 files (optional, if not provided returns base64)
        
        Returns:
            JSON response with conversion results
        """
        language = request.json.get('language', 'id') if request.json else 'id'
        slow = request.json.get('slow', False) if request.json else False
        output_dir = request.json.get('output_dir') if request.json else None
        
        try:
            result = tts_service.convert_chunks_to_speech(
                module_id=module_id,
                language=language,
                slow=slow,
                output_dir=output_dir
            )
            
            # If audio buffers are returned (not saved to files), convert to base64
            if result.get('success') and not output_dir:
                for item in result.get('results', []):
                    if 'audio_buffer' in item:
                        audio_data = item['audio_buffer'].getvalue()
                        item['audio_base64'] = base64.b64encode(audio_data).decode('utf-8')
                        del item['audio_buffer']
            
            return TTSHandler.success_response(result, 'Chunks converted to speech successfully', 200)
        except Exception as e:
            return TTSHandler.error_response(str(e), 500)
    
    @staticmethod
    def convert_chunk_to_speech(chunk_id):
        """
        Convert a single chunk to MP3 audio
        
        Path parameter:
            - chunk_id: Chunk ID to convert
        
        Query parameters (GET) or JSON body (POST):
            - language: Language code (default 'id' for Indonesian)
            - slow: Speak slowly (default False)
            - format: Response format - 'file' to download, 'json' for base64 (default 'file')
        
        Returns:
            MP3 audio file or JSON with base64 encoded audio
        """
        if request.method == 'GET':
            language = request.args.get('language', 'id')
            slow = request.args.get('slow', 'false').lower() == 'true'
            response_format = request.args.get('format', 'file')
        else:
            language = request.json.get('language', 'id') if request.json else 'id'
            slow = request.json.get('slow', False) if request.json else False
            response_format = request.json.get('format', 'file') if request.json else 'file'
        
        try:
            result = tts_service.convert_single_chunk_to_speech(
                chunk_id=chunk_id,
                language=language,
                slow=slow
            )
            
            if not result.get('success'):
                return TTSHandler.not_found_response(result.get('message', 'Chunk not found'))
            
            audio_buffer = result['audio_buffer']
            
            # Return as file download
            if response_format == 'file':
                audio_buffer.seek(0)
                return send_file(
                    audio_buffer,
                    mimetype='audio/mpeg',
                    as_attachment=True,
                    download_name=f'chunk_{chunk_id}.mp3'
                )
            else:
                # Return as JSON with base64
                audio_data = audio_buffer.getvalue()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                return TTSHandler.success_response(
                    {"audio_base64": audio_base64},
                    f"Successfully converted chunk {chunk_id} to speech",
                    200
                )
        except Exception as e:
            return TTSHandler.error_response(str(e), 500)
    
    @staticmethod
    def convert_text_to_speech():
        """
        Convert arbitrary text to MP3 audio
        
        JSON body:
            - text: Text to convert (required)
            - language: Language code (default 'id' for Indonesian)
            - slow: Speak slowly (default False)
            - format: Response format - 'file' to download, 'json' for base64 (default 'file')
        
        Returns:
            MP3 audio file or JSON with base64 encoded audio
        """
        if not request.json or 'text' not in request.json:
            return TTSHandler.error_response("Missing 'text' in request body", 400)
        
        text = request.json.get('text')
        language = request.json.get('language', 'id')
        slow = request.json.get('slow', False)
        response_format = request.json.get('format', 'file')
        
        try:
            audio_buffer = tts_service.convert_text_to_speech(
                text=text,
                language=language,
                slow=slow
            )
            
            # Return as file download
            if response_format == 'file':
                audio_buffer.seek(0)
                return send_file(
                    audio_buffer,
                    mimetype='audio/mpeg',
                    as_attachment=True,
                    download_name='speech.mp3'
                )
            else:
                # Return as JSON with base64
                audio_data = audio_buffer.getvalue()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                return TTSHandler.success_response(
                    {"audio_base64": audio_base64},
                    "Successfully converted text to speech",
                    200
                )
        except Exception as e:
            return TTSHandler.error_response(str(e), 500)


# Create handler instance
tts_handler = TTSHandler()


# Register routes
@tts_bp.route('/tts/module/<int:module_id>', methods=['POST'])
def convert_module_to_speech(module_id):
    """Convert all chunks from a module to MP3 files"""
    return tts_handler.convert_module_to_speech(module_id)


@tts_bp.route('/tts/chunk/<int:chunk_id>', methods=['GET', 'POST'])
def convert_chunk_to_speech(chunk_id):
    """Convert a single chunk to MP3 audio"""
    return tts_handler.convert_chunk_to_speech(chunk_id)


@tts_bp.route('/tts/text', methods=['POST'])
def convert_text_to_speech():
    """Convert arbitrary text to MP3 audio"""
    return tts_handler.convert_text_to_speech()
