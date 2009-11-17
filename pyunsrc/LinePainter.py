class LinePainter(object):
    def __init__(self):
        self._lines = []
        self._cur_line = []
    def end_line(self):
        self._lines.append(self._cur_line)
        self._cur_line = []
    def put(self, element):
        self._cur_line.append(element)
    def draw(self, surface, pos):
        y = pos[1]
        for line in self._lines:
            x = pos[0]
            line_height = max([0] + [line_surface.get_height() for line_surface in line])
            for element in line:
                surface.blit(element, (x, y + (line_height - element.get_height()) / 2))
                x += element.get_width()
            y += line_height
    def size(self):
        width = height = 0
        for line in self._lines:
            height += max([0] + [surface.get_height() for surface in line])
            width = max(width, sum([surface.get_width() for surface in line]))
        return width, height
