'''
本脚本的目的是进行批量的替换
思路是选出每一个问/答下面的内容，
'''
from project.PDFbookmark import PDF

if __name__ == "__main__":
    P = PDF()
    P.add_bookmark()
    if P.need_add_watermark:P.add_watermark()
    if P.need_add_encrypt:P.add_encrypt()
    P.save_pdf()