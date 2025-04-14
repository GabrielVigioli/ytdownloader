from django.shortcuts import render
from pytubefix import YouTube
from pytube.exceptions import RegexMatchError
from django.http import FileResponse
import os
from moviepy import VideoFileClip, AudioFileClip
import re
import shutil
import threading
import uuid


def limpar_pasta(caminho_pasta):
    if os.path.exists(caminho_pasta):
        shutil.rmtree(caminho_pasta)


def limpar_nome_arquivo(nome):
    nome = nome.replace(" ", "_")
    nome = re.sub(r"[\'\"\\\/\:\*\?\<\>\|\(\)\[\]\{\}]", "", nome)
    return nome


def index(request):
    context = {
        "yt": None,
        "title": None,
        "videolink": None,
        "error": None,
        "choose": None,
        "stream": None,
    }

    if request.method == "POST":
        videolink = request.POST.get("videolink")
        if videolink:
            try:
                yt = YouTube(videolink)
                video_id = str(uuid.uuid4())[:8] 
                temp_dir = os.path.join("temp", video_id)
                os.makedirs(temp_dir, exist_ok=True)

                context["yt"] = yt
                context["title"] = yt.title
                context["videolink"] = videolink
                choose = request.POST.get("choose")
                context["choose"] = choose

                filename_base = yt.title

                if choose:
                    if choose in ["360", "480", "720", "1080"]:
                        resolution = choose
                        finalname = (
                            f"{limpar_nome_arquivo(filename_base)}_{resolution}p.mp4"
                        )
                        filename = f"videoinput_{video_id}.mp4"
                        audioname = f"audioinput_{video_id}.mp4"

                        filepath = os.path.join(temp_dir, finalname)

                        stream = yt.streams.filter(res=resolution + "p").first()
                        stream_audio = yt.streams.filter(
                            file_extension="mp4", only_audio=True
                        ).first()

                        if stream and stream_audio:
                            stream.download(output_path=temp_dir, filename=filename)
                            stream_audio.download(
                                output_path=temp_dir, filename=audioname
                            )

                            video_clip = VideoFileClip(os.path.join(temp_dir, filename))
                            audio_clip = AudioFileClip(
                                os.path.join(temp_dir, audioname)
                            )

                            final_clip = video_clip.with_audio(audio_clip)
                            final_clip.write_videofile(filepath, codec="libx264")

                            response = FileResponse(
                                open(filepath, "rb"),
                                as_attachment=True,
                                filename=finalname,
                            )

                            threading.Timer(
                                30.0, limpar_pasta, args=(temp_dir,)
                            ).start()

                            video_clip.close()
                            audio_clip.close()
                            final_clip.close()

                            return response

                        else:
                            context["error"] = (
                                f"No stream found with {resolution}p resolution."
                            )

                    elif choose == "audiom4a":
                        audioname = f"{limpar_nome_arquivo(filename_base)}_audio.m4a"
                        filepath = os.path.join(temp_dir, audioname)
                        stream = yt.streams.get_audio_only()
                        stream.download(output_path=temp_dir, filename=audioname)

                        response = FileResponse(
                            open(filepath, "rb"),
                            as_attachment=True,
                            filename=audioname,
                        )
                        threading.Timer(30.0, limpar_pasta, args=(temp_dir,)).start()
                        return response

                    elif choose == "audiomp4":
                        audioname = f"{limpar_nome_arquivo(filename_base)}_audio.mp4"
                        filepath = os.path.join(temp_dir, audioname)
                        stream = yt.streams.filter(
                            file_extension="mp4", only_audio=True
                        ).first()
                        stream.download(output_path=temp_dir, filename=audioname)

                        response = FileResponse(
                            open(filepath, "rb"),
                            as_attachment=True,
                            filename=audioname,
                        )
                        threading.Timer(30.0, limpar_pasta, args=(temp_dir,)).start()
                        return response

            except Exception as e:
                print("Erro:", e)
                context["error"] = "Ocorreu um erro ao processar o link."

        else:
            context["error"] = "Por favor, insira um link válido."

    return render(request, "index.html", context)
