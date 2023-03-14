import os, sys
from .PyPDF2 import pdf

PdfFileReader = pdf.PdfFileReader
PdfFileWriter = pdf.PdfFileWriter

dir1 = ""
dir2 = r"C:\备份\数学书\线性代数六百证明题详解.pdf"
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
Entrance = os.path.abspath(".")
bookmarkstxt_backup_dir = os.path.join(THIS_FOLDER,"书签记录")

bookmarktxtli = os.path.join(Entrance, 'bookmarkli.txt')

dir4 = r"C:\备份\数学书\看考研\考研数学历年真题\真题大全解解析（数3）_书签.pdf"
watermark_dir = os.path.join(THIS_FOLDER, "试练之地群号PDF书签宣传.pdf")
# watermark_dir=os.path.join(THIS_FOLDER, "试练之地群号PDF书签宣传 old 2.pdf")

pswd = "lqqzloz7lqq6ogog"
shift = 9
# add_watermark=False
# encrypt=False
statearray = ["正常", #0
              "书签格式错误!请检查", #1
              "书签页码超出实际页码错误!请检查", #2
              "错误,原因:bookmarkli.txt不存在或格式不正确!请:\n"
              "1在本程序根目录下新建名为bookmarkli.txt的文件,\n" 
              "2在第一行写入符合格式的pdf绝对路径,第二行写入页码偏移量,第三行开始写入符合格式的目录书签!", #3
              "错误,原因:bookmarkli.txt中第一行不是pdf绝对路径,或pdf不存在!",#4
              "错误,原因:bookmarkli.txt中第二行不是页码偏移量,请在第二行输入一个非负整数!", #5
              "错误,原因:bookmarkli.txt中没有目录信息"
              ]

class Error(Exception):
    def __init__(self,ecode):
        self.ecode=ecode

    def __str__(self):
        return statearray[self.ecode]

class PDF:
    def __init__(self):
        self.path, self.pageoffset, self.need_add_watermark, self.need_add_encrypt, self.bookmarkli=self.get_configuration()
        self.reader = PdfFileReader(open(self.path, "rb"), strict=False)
        self.writer = PdfFileWriter()
        self.writer.appendPagesFromReader(self.reader)
        self.writer.addMetadata(self.reader.getDocumentInfo())
        self.watermark = PdfFileReader(open(watermark_dir, "rb"))
        self.totalpages = self.reader.getNumPages()
        self.toc_shift = self.calc_pageoffset()
        print("PDF页数:" + str(self.totalpages))
        print("添加水印:" + str(self.need_add_watermark))
        print("加密:" + str(self.need_add_encrypt))
        pass
    def get_configuration(self):
        """pdfpath, pageoffset, bookmarkli, """
        add_watermark,add_encrypt =False,False
        if (not os.path.exists(bookmarktxtli)):
            raise Error(3)
        lines = open(bookmarktxtli,"r",encoding="utf-8").readlines()
        lines = [ line.replace("\n","") for line in lines]
        if len(lines)<3:
            raise Error(3)
        pdfpath = lines[0]
        print(f"文件地址={pdfpath}")
        if not os.path.isfile(pdfpath) or not os.path.exists(pdfpath):
            raise Error(4)
        if lines[1].isnumeric() and int(lines[1])>=0:
            pageoffset = lines[1]
        else:
            info = lines[1].split(" ")
            if len(info) == 1:
                raise Error(5)
            pageoffset = info[0]
            if len(info)==2 and info[1] not in {"0",""}:
                add_watermark =True
            if len(info)==3 and info[2] not in {"0",""}:
                add_encrypt = True

        return (pdfpath,pageoffset,add_watermark,add_encrypt,lines[2:])

    @property
    def new_path(self):
        name, ext = os.path.splitext(self.path)
        return name + '_书签' + ext
    def calc_pageoffset(self):
        shift_old = int(self.pageoffset)
        if self.reader.xrefIndex == 0:
            tocShift = shift_old  # 如果是从0开始计数,直接用,不是的话将偏移-1
        else:
            print("xrefIndex effected")
            tocShift = shift_old  # 这个地方还需要继续修复,我不清楚这个到底意味着什么.
            '''
            16+1-2=15, 这是预期的,但是得到的结果是17,所以不该加1,加1为16,
            因为 ,根据实验, 目录中的页码为1,偏移为0时,PDF中的页码为2,也就是说,从0计数, 目录页码为1就是01,是PDF页码中的第二个数,
            为了得到PDF页码中的第10个数,也就是PDF页码为10,那么插入的书签数为9,因为0到9一共10个数,
            而书签本身就已经有1,所以为了得到9,偏移量得是8,现在我已经将书签本身的偏移减一对应,那么输入的偏移只要再减一即可.
            '''
        tocShift -= 1
        return tocShift
    def add_bookmark(self) -> object:
        '''
        '''
        parent = None
        last = []
        stack = []
        for line in self.bookmarkli:
            # 获取信息,缩进,名称,页码
            now = line.split("\t")
            print(now)
            if (len(now) < 2):
                raise Error(1)
            if (int(now[-1]) + shift > self.totalpages):
                raise Error(2)
            # 设计差值
            val = len(now[:-2]) - len(last)
            # 如果差值大于0,表明now是last的子书签,将parent压栈.
            if (val > 0):
                stack.append(parent)
            # 如果差值小于等于0,表明当前的书签不是last的子书签,要退栈,退val+1次,
            # 0=平级,享有共同的祖先,不操作parent与stack
            else:
                for p in range(0, -(val)):
                    stack.pop()
            parent = stack[-1] if len(stack) > 0 else None
            # 插入书签
            parent = self.writer.addBookmark(now[-2], int(now[-1]) - 1 + self.toc_shift, parent)
            last = now[:-2]
            print("append bookmark " + now[-2] + "at " + now[-1])

        return self
    def add_watermark(self):
        self.writer.getPage(0).mergePage(self.watermark.getPage(0))
        print("已添加水印")

    def add_encrypt(self):
        self.writer.encrypt(user_pwd="", owner_pwd=pswd)
        '''
        此处对PYPDF2源代码做了修改
        https://www.biopdf.com/guide/pdf_permissions.php
        D:\Anaconda\Lib\site-packages\PyPDF2\pdf.py#423行
        https://blog.csdn.net/he99774/article/details/103153249
        32位二进制,在指定位置上加表格上的字即可
        P = -1 改为 P = -3372
        '''
        print("已加密")

    def save_pdf(self):
        name = os.path.basename(self.new_path) + ".txt"
        curname = os.path.join(bookmarkstxt_backup_dir, name)
        print("正保存目录txt到" + curname)
        if (os.path.exists(curname)):
            print(curname + "已存在,删除重建")
            os.remove(curname)
        g = open(os.path.join(THIS_FOLDER, name), "a", encoding="utf-8")
        g.write("\n".join(self.bookmarkli))
        g.close()
        print("目录TXT写入完成")
        print("最后一步,生成带书签PDF中")
        with open(self.new_path, 'wb') as out:
            self.writer.write(out)
        print("带书签PDF生成完成,地址在" + self.new_path)

class Pdf(object):
    def __init__(self, path):
        self.path = path
        self.reader = PdfFileReader(open(path, "rb"), strict=False)
        self.writer = PdfFileWriter()
        self.watermark = PdfFileReader(open(watermark_dir, "rb"))
        self.totalpages = self.reader.getNumPages()
        print("PDF文件名:" + path + "\nPDF页数:" + str(self.totalpages))
        self.statearray = ["正常", "格式错误!请检查", "页码错误!请检查", "请在本程序目录下新建名为bookmarkli.txt的文件,并往其中写入符合格式的目录书签!"]
        self.statecode = 0
        self.bookmark = None

    @property
    def new_path(self):
        name, ext = os.path.splitext(self.path)
        return name + '_书签' + ext

    # def add_bookmark(self, title, pagenum, parent=None):
    #     self.writer.addBookmark(title, pagenum, parent=parent)
    #     return self
    def add_bookmark(self, bookmarkpath, shift_old_old: str = 0, add_watermark=True,encrypt=True) -> object:

        '''

        :param bookmarkpath:
        :param shift_old_old: 页码的偏移量,我希望能指哪打哪,好好分析.
        :param add_watermark:
        :return:
        '''
        pageShift = -1  # PDF从0开始计数
        print(f"当前bookmarkli.txt地址为:{bookmarkpath}")
        if (not os.path.exists(bookmarkpath)):
            self.statecode = 3
            return self
        self.writer.appendPagesFromReader(self.reader)
        self.writer.addMetadata(self.reader.getDocumentInfo())
        with open(bookmarkpath, 'rb') as f:
            print("txt书签路径:" + bookmarkpath)
            print("添加水印:"+str(add_watermark))
            print("加密:"+str(encrypt))
            shift_old = int(shift_old_old)  # 从参数传入的时候是字符串
            if self.reader.xrefIndex == 0:
                tocShift = shift_old  # 如果是从0开始计数,直接用,不是的话将偏移-1
            else:
                print("xrefIndex effected")
                tocShift = shift_old  # 这个地方还需要继续修复,我不清楚这个到底意味着什么.
                '''
                16+1-2=15, 这是预期的,但是得到的结果是17,所以不该加1,加1为16,
                '''
            tocShift -= 1
            '''
            因为 ,根据实验, 目录中的页码为1,偏移为0时,PDF中的页码为2,也就是说,从0计数, 目录页码为1就是01,是PDF页码中的第二个数,
            为了得到PDF页码中的第10个数,也就是PDF页码为10,那么插入的书签数为9,因为0到9一共10个数,
            而书签本身就已经有1,所以为了得到9,偏移量得是8,现在我已经将书签本身的偏移减一对应,那么输入的偏移只要再减一即可.
            '''

            lines = f.readlines()
            self.bookmark = {"path": bookmarkpath, "content": lines.copy()}
            parent = None
            last = []
            stack = []
            for line in lines:
                # 获取信息,缩进,名称,页码
                now = line.decode("utf-8").split("\t")
                print(now)
                if (len(now) < 2):
                    self.statecode = 1
                    return self
                if (int(now[-1]) + shift > self.totalpages):
                    self.statecode = 2
                    return self
                # 设计差值
                val = len(now[:-2]) - len(last)
                # 如果差值大于0,表明now是last的子书签,将parent压栈.
                if (val > 0):
                    stack.append(parent)
                # 如果差值小于等于0,表明当前的书签不是last的子书签,要退栈,退val+1次,
                # 0=平级,享有共同的祖先,不操作parent与stack
                else:
                    for p in range(0, -(val)):
                        stack.pop()
                parent = stack[-1] if len(stack) > 0 else None
                # 插入书签
                parent = self.writer.addBookmark(now[-2], int(now[-1]) + pageShift + tocShift, parent)
                last = now[:-2]
                print("append bookmark " + now[-2] + "at " + now[-1])
        if add_watermark:  # 默认添加水印,也可以去掉,参数里加个false就好了,平时都是要加的
            self.writer.getPage(0).mergePage(self.watermark.getPage(0))
            print("已添加水印")
        if encrypt:
            self.writer.encrypt(user_pwd="", owner_pwd=pswd)
            '''
            此处对PYPDF2源代码做了修改
            https://www.biopdf.com/guide/pdf_permissions.php
            D:\Anaconda\Lib\site-packages\PyPDF2\pdf.py#423行
            https://blog.csdn.net/he99774/article/details/103153249
            32位二进制,在指定位置上加表格上的字即可
            P = -1 改为 P = -3372
            '''
            print("已加密")
        return self

    def make_watermark(self):

        return self

    def save_pdf(self):
        if (self.statecode > 0):
            print(self.statearray[self.statecode])
            return -1
        name = os.path.basename(self.new_path) + ".txt"
        curname = os.path.join(THIS_FOLDER, name)
        print("正保存目录到" + curname)
        if (os.path.exists(curname)):
            print(curname + "已存在,删除重建")
            os.remove(curname)
        g = open(os.path.join(THIS_FOLDER, name), "a", encoding="utf-8")
        for c in self.bookmark["content"]:
            g.write(c.decode("utf-8"))
        g.close()
        print("目录TXT写入完成")
        print("最后一步,生成带书签PDF中")
        with open(self.new_path, 'wb') as out:
            self.writer.write(out)
        print("带书签PDF生成完成,地址在" + self.new_path)


# def main():
#     if len(sys.argv) > 1:
#         print(
#             '''
#             欢迎使用书签生成脚本,可以添加单个书签,也可以批量添加书签.
#             但是要搞清楚,你想覆盖原有书签还是追加新的书签.
#             '''
#         )
#         if os.path.exists(sys.argv[1]):
#             pdfpath = sys.argv[1]
#             pageoffset = sys.argv[2] if len(sys.argv)>=3 else "0"
#             add_watermark = True if len(sys.argv)>=4 else False
#             encrypt = True if len(sys.argv)>=5 else False
            
#             Pdf(pdfpath).add_bookmark(bookmarktxtli, pageoffset,add_watermark,encrypt).save_pdf()
#         else:
#             print(sys.argv[1] + "文件不存在,请检查是否可能出现格式不匹配问题")
#             return
#     else:
#         if dir1 == "":  # 这个是通过修改文件读取的PDF地址
#             print("请添加文件参数!")
#             return
        
#         # Pdf(dir1).add_bookmark(bookmarktxtli, shift,add_watermark,encrypt).save_pdf()
#         # print(P.reader.xrefIndex)


if __name__ == '__main__':
    # main()
    print("请通过命令行运行本文件")
