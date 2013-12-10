felipecorrea@my:/var/www/video$ sudo ffmpeg -i WP_20130806_135146Z.mp4 -acodec libmp3lame -ac 2 -ab 16k -ar 48000 -vn m.mp3
felipecorrea@my:/var/www/video$ for i in WP*.mp4; do echo $i; echo ${i%.mp4}; done;

###If you have a lot of files to convert run this command in the directory where your wma files reside
###convert wma to ogg
###for i in *.wma; do ffmpeg -i $i -acodec vorbis -aq 100 ${i%.wma}.ogg; done
###convert wma to mp3
###for i in *.wma; do ffmpeg -i $i -acodec mp3 -aq 100 ${i%.wma}.mp3; done

#video to ogg audio
#for i in WP*.mp4; do sudo ffmpeg -i $i -acodec libvorbis -ac 2 -ab 16k -ar 48000 -vn ${i%.mp4}-audio.ogg; done
for i in WP*.mp4; do sudo ffmpeg -i $i -acodec libvorbis -vn ${i%.mp4}-audio.ogg; done

#video to mp3 audio
for i in WP*.mp4; do ffmpeg -i $i -acodec libmp3lame -ac 2 -ab 16k -ar 48000 -vn ${i%.mp4}-audio.mp3; done


