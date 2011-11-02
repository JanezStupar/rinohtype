
from psg.drawing.box import canvas, eps_image

from .flowable import Flowable
from .number import format_number
from .number.style import NUMBER
from .paragraph import Paragraph, ParagraphStyle
from .text import StyledText
from .unit import mm


class Image(Flowable):
    def __init__(self, filename, scale=1.0, style=None):
        super().__init__(style)
        self.filename = filename
        self.scale = scale

    def render(self, pscanvas, offset=0):
        buffer = canvas(pscanvas, 0, 0, pscanvas.w(), pscanvas.h())
        eps = eps_image(buffer, open(self.filename, 'rb'), document_level=True)
        image_height = eps.h() * self.scale
        image_width = eps.w() * self.scale
        image_canvas = canvas(pscanvas, (pscanvas.w() - image_width) / 2,
                              pscanvas.h() - offset - image_height,
                              pscanvas.w(), pscanvas.h())
        buffer.write_to(image_canvas)
        image_canvas.append(eps)
        image_canvas.push('{0} {0} scale'.format(self.scale))
        image_canvas.write_to(pscanvas)

        return image_height


class CaptionStyle(ParagraphStyle):
    attributes = {'numberingStyle': NUMBER,
                  'numberingSeparator': '.'}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class Caption(Paragraph):
    style_class = CaptionStyle

    next_number = {}

    def __init__(self, category, text, style=None):
        super().__init__('', style)
        next_number = self.next_number.setdefault(category, 1)
        numbering_style = self.get_style('numberingStyle')
        numbering_sep = self.get_style('numberingSeparator')
        if numbering_style is not None:
            self.ref = format_number(self.next_number[category],
                                     numbering_style)
            number = self.ref + numbering_sep + '&nbsp;'
        else:
            self.ref = None
            number = ''
        styled_text = StyledText(category + ' ' + number + text)
        styled_text.parent = self
        self.append(styled_text)


class Figure(Flowable):
    def __init__(self, filename, caption, scale=1.0, style=None,
                 captionstyle=None):
        super().__init__(style)
        self.filename = filename
        self.scale = scale
        self.caption = Caption('Figure', caption, captionstyle)

    def render(self, pscanvas, offset=0):
        image = Image(self.filename, scale=self.scale)
        height = image.render(pscanvas, offset)
        height += self.caption.render(pscanvas, offset + height)
        return height
