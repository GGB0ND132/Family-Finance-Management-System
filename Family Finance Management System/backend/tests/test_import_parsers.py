import io

from openpyxl import Workbook

from app.modules.imports.parsers import parse_file


def test_parse_alipay_csv_skips_statement_preamble():
    data = "\n".join(
        [
            "------",
            "导出信息：",
            "共1笔记录",
            "------------------------支付宝支付科技有限公司  电子客户回单------------------------",
            "交易时间,交易分类,交易对方,对方账号,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商家订单号,备注,",
            "2026-09-01 18:01:16,日用百货,便利店,/,饮料,支出,13.14,银行卡,交易成功,order,,,",
        ]
    ).encode("gbk")

    rows = parse_file(data, "alipay.csv")

    assert rows == [
        {
            "交易时间": "2026-09-01 18:01:16",
            "交易分类": "日用百货",
            "交易对方": "便利店",
            "对方账号": "/",
            "商品说明": "饮料",
            "收/支": "支出",
            "金额": "13.14",
            "收/付款方式": "银行卡",
            "交易状态": "交易成功",
            "交易订单号": "order",
            "商家订单号": "",
            "备注": "",
            "": "",
        }
    ]


def test_parse_wechat_xlsx_finds_detail_header_after_preamble():
    workbook = Workbook()
    sheet = workbook.active
    for row in range(1, 18):
        sheet.cell(row, 1).value = "微信支付账单说明"
    sheet.append(
        ["交易时间", "交易类型", "交易对方", "商品", "收/支", "金额(元)", "支付方式", "当前状态", "交易单号", "商户单号", "备注"]
    )
    sheet.append(
        ["2026-09-01 17:30:56", "转账", "好友", "转账备注", "收入", 32.75, "/", "已存入零钱", "order", "/", "/"]
    )
    stream = io.BytesIO()
    workbook.save(stream)

    rows = parse_file(stream.getvalue(), "wechat.xlsx")

    assert rows[0]["交易时间"] == "2026-09-01 17:30:56"
    assert rows[0]["金额(元)"] == "32.75"
    assert rows[0]["收/支"] == "收入"
