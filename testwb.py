from pdfminer.layout import LAParams, LTTextBox, LTTextLine
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator

#<LTTextLineHorizontal 7.087,451.618,575.887,464.866 '     VALENCIA, SPAIN                                                           \n'>
#<LTTextLineHorizontal 7.087,427.618,575.887,440.866 '     BRISBANE, AUSTRALIA                                                       \n'>
#<LTTextLineHorizontal 7.087,451.618,575.887,464.866 '     VALENCIA                                                                  \n'>
#<LTTextLineHorizontal 7.087,427.618,575.887,440.866 '     MELBOURNE, AUSTRALIA                                                      \n'>
files = ["MCOP0101_651482249.pdf", "MCOP0101_651482615.pdf"]
for file in files:
    fp = open(file, 'rb')
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pages = PDFPage.get_pages(fp)
    interpreter.process_page(next(pages))
    layout = device.get_result()
    for lobj in layout:
        #print(lobj)
        if isinstance(lobj, LTTextBox) and 7<=lobj.bbox[0]<=8 and 16<=lobj.bbox[1]<=17:
            #print(lobj)
            #print(lobj[15])
            for line in lobj:
                if isinstance(line, LTTextLine):
                    if 7<=line.bbox[0]<=8 and 451<=line.bbox[1]<=452:
                        print("Origin: %s"%line.get_text().strip())
                    if 7<=line.bbox[0]<=8 and 427<=line.bbox[1]<=428:
                        print("Dest: %s"%line.get_text().strip())
                    #print(type(line))
                    #print(line.get_text())
                    #for char in line:
                    #    print(type(char))
                    #print(len(line))
                    #print("%s %s %s"%(lobj.bbox[0], lobj.bbox[3],  lobj.bbox[4]))
        #if isinstance(lobj, LTLine):
        #    print(lobj)
        #    print(lobj.get_text())
            #for line in lobj.get_text():
            #    print(line)
        #x, y, text = lobj.bbox[0], lobj.bbox[3], lobj.get_text()
        #print('At %r is text: %s' % ((x, y), text))
        #if isinstance(lobj, LTTextBox):
        #    x, y, text = lobj.bbox[0], lobj.bbox[3], lobj.get_text()
        #    print('At %r is text: %s' % ((x, y), text))