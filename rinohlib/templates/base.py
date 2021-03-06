
from rinoh.dimension import PT, CM
from rinoh.document import Document, DocumentPart, Page, PORTRAIT
from rinoh.layout import (Container, FootnoteContainer, Chain,
                          UpExpandingContainer, DownExpandingContainer)
from rinoh.paper import A4
from rinoh.reference import Variable, PAGE_NUMBER, SECTION_NUMBER, SECTION_TITLE, \
    NUMBER_OF_PAGES
from rinoh.structure import Section, Heading, TableOfContents, Header, Footer
from rinoh.text import Tab
from rinoh.util import NotImplementedAttribute

from ..stylesheets.somestyle import stylesheet as STYLESHEET


# page definitions
# ----------------------------------------------------------------------------

class SimplePage(Page):
    header_footer_distance = 14*PT
    column_spacing = 1*CM

    def __init__(self, chain, paper, orientation):
        super().__init__(chain.document_part, paper, orientation)
        h_margin = self.document.options['page_horizontal_margin']
        v_margin = self.document.options['page_vertical_margin']
        num_cols = self.document.options['columns']
        body_width = self.width - (2 * h_margin)
        body_height = self.height - (2 * v_margin)
        total_column_spacing = self.column_spacing * (num_cols - 1)
        column_width = (body_width - total_column_spacing) / num_cols
        self.body = Container('body', self, h_margin, v_margin,
                              body_width, body_height)

        footnote_space = FootnoteContainer('footnotes', self.body, 0*PT,
                                           body_height)
        self.columns = [Container('column{}'.format(i + 1), self.body,
                                  left=i * (column_width + self.column_spacing),
                                  top=0*PT,
                                  width=column_width,
                                  bottom=footnote_space.top,
                                  chain=chain)
                        for i in range(num_cols)]
        footnote_space.max_height = body_height - self.columns[0]._cursor
        for column in self.columns:
            column._footnote_space = footnote_space

        if self.document_part.header:
            header_bottom = self.body.top - self.header_footer_distance
            self.header = UpExpandingContainer('header', self,
                                               left=h_margin,
                                               bottom=header_bottom,
                                               width=body_width)
            self.header.append_flowable(Header(self.document_part.header))
        if self.document_part.footer:
            footer_vpos = self.body.bottom + self.header_footer_distance
            self.footer = DownExpandingContainer('footer', self,
                                                 left=h_margin,
                                                 top=footer_vpos,
                                                 width=body_width)
            self.footer.append_flowable(Footer(self.document_part.footer))


# document sections & parts
# ----------------------------------------------------------------------------

class BookPart(DocumentPart):
    header = None
    footer = None

    def __init__(self, document_section):
        super().__init__(document_section)
        self.chain = Chain(self)
        for flowable in self.flowables():
            self.chain << flowable

    def flowables(self):
        raise NotImplementedError

    def first_page(self):
        return self.new_page([self.chain])

    def new_page(self, chains):
        chain, = chains
        return SimplePage(chain, self.document.options['page_size'],
                          self.document.options['page_orientation'])


class TableOfContentsSection(Section):
    def __init__(self):
        super().__init__([Heading('Table of Contents', style='unnumbered'),
                          TableOfContents()],
                         style='table of contents')

    def prepare(self, document):
        self.id = document.metadata.get('toc_id')
        super().prepare(document)


class TableOfContentsPart(BookPart):
    footer = Tab() + Variable(PAGE_NUMBER)

    def flowables(self):
        yield TableOfContentsSection()


class ContentsPart(BookPart):
    @property
    def header(self):
        return self.document.options['header_text']

    @property
    def footer(self):
        return self.document.options['footer_text']

    def flowables(self):
        return self.document.content_flowables

    def prepare(self):
        pass


class DocumentOptions(dict):
    options = {'stylesheet': STYLESHEET,
               'page_size': A4,
               'page_orientation': PORTRAIT,
               'page_horizontal_margin': 2*CM,
               'page_vertical_margin': 3*CM,
               'columns': 1,
               'header_text': (Variable(SECTION_NUMBER(1)) + ' '
                               + Variable(SECTION_TITLE(1))),
               'footer_text': Tab() + Variable(PAGE_NUMBER)
                              + '/' + Variable(NUMBER_OF_PAGES)}

    def __init__(self, **options):
        for name, value in options.items():
            self._get_default(name)
            self[name] = value

    def _get_default(self, name):
        for cls in type(self).__mro__:
            try:
                return cls.options[name]
            except KeyError:
                continue
            except AttributeError:
                raise ValueError("Unknown option '{}'".format(name))

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return self._get_default(key)


class DocumentBase(Document):
    sections = NotImplementedAttribute()
    options_class = DocumentOptions

    def __init__(self, content_flowables, options=None, backend=None):
        self.options = options or self.options_class()
        super().__init__(content_flowables, self.options['stylesheet'],
                         backend=backend)
