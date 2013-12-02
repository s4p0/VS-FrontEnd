import pdb
import os
import Image

sizes = [(75,75), (120,120), (400,400)]
top_dir = "/home/felipecorrea/Dropbox/ForestWatchers/web/pyserver/api/static/uploads"

images = [x for x in os.listdir(top_dir)]

for img in images:
	for size in sizes:
		dir = os.path.join(top_dir, 'thumb_%r' % size[0])

		try:
			if not os.path.exists(dir):
				os.makedirs(dir)
			filename = os.path.join(dir, img)
			# filename = os.path.join(top_dir, 'thumb_%r' % size[0], img)
			if not os.path.isfile(filename):
				# pdb.set_trace()
				im = Image.open(os.path.join(top_dir, img))
				im.thumbnail(size)
				im.save(filename)
		except:
			print filename


# # files = ['a.jpg','b.jpg','c.jpg']

# for image in files:
#     for size in sizes:
#       Image.open(image).thumbnail(size).save("thumbnail_%s" % image)