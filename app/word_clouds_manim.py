import json

from manim import *


class ImageSlideshow(Scene):
    def construct(self):
        with open('/tmp/for_manim.txt', 'r') as f:
            config = json.loads(f.read())
        paths = list(sorted(config['images'], key=lambda item: int(item['year'])))
        duration = int(config['year_duration'])
        for path in paths:
            image = ImageMobject(path['path'])
            text = Text(str(path['year']), color=BLACK, font_size=24).to_edge(DOWN)
            text.to_corner(DOWN + RIGHT, buff=0.2)
            self.add(image, text)
            self.wait(duration)
            self.remove(image, text)
