from modules.base import BaseModule, ReportThread, apply_excel_style
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QHeaderView, QMessageBox, QProgressDialog
from PyQt5.QtCore import Qt
import pandas as pd
import tempfile
import os

def process_income(df, adjustments=None):
    required_cols = ['日期', '收入金额']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f'缺少必需列：{col}')
    df['日期'] = pd.to_datetime(df['日期'])
    df['月份'] = df['日期'].dt.to_period('M').astype(str)
    monthly = df.groupby('月份')['收入金额'].sum().reset_index()
    monthly.rename(columns={'收入金额': '月度总收入'}, inplace=True)
    monthly['月度总收入'] = monthly['月度总收入'].round()
    monthly['环比增长率(%)'] = monthly['月度总收入'].pct_change() * 100
    monthly['环比增长率(%)'] = monthly['环比增长率(%)'].round(2)
    return monthly

class IncomeModule(BaseModule):
    def init_ui(self):
        layout = QVBoxLayout(self)

        self.upload_label = QLabel("📂 点击或拖拽 Excel 文件至此\n（自动读取第一个sheet）")
        self.upload_label.setAlignment(Qt.AlignCenter)
        self.upload_label.setStyleSheet("border: 2px dashed #aaa; border-radius: 10px; padding: 30px; background-color: #ffffff; color: #000000;")
        self.upload_label.setMinimumHeight(120)
        self.upload_label.mousePressEvent = lambda e: self.select_file()
        layout.addWidget(self.upload_label)

        preview_label = QLabel("数据预览（前100行）")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(preview_label)
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.preview_table)

        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("📎 生成报表")
        self.download_btn = QPushButton("⬇️ 下载报表")
        self.download_btn.setEnabled(False)
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.download_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.generate_btn.clicked.connect(self.start_generate)
        self.download_btn.clicked.connect(self.save_report)

        self.report_thread = None

    def on_file_loaded(self, df):
        self.preview_data(df.head(100))
        self.download_btn.setEnabled(False)
        self.current_report_path = None

    def preview_data(self, df):
        self.preview_table.clear()
        if df.empty:
            return
        self.preview_table.setRowCount(df.shape[0])
        self.preview_table.setColumnCount(df.shape[1])
        self.preview_table.setHorizontalHeaderLabels(df.columns.astype(str))
        for i, row in df.iterrows():
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                self.preview_table.setItem(i, j, item)
        self.preview_table.resizeColumnsToContents()

    def start_generate(self):
        if self.current_df is None:
            QMessageBox.warning(self, "无数据", "请先上传Excel文件")
            return
        self.generate_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.report_thread = ReportThread(process_income, self.current_df)
        self.report_thread.finished.connect(self.on_generate_finished)
        self.report_thread.error.connect(self.on_generate_error)
        self.report_thread.start()
        self.progress = QProgressDialog("正在生成报表，请稍候...", None, 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()

    def on_generate_finished(self, result):
        self.progress.close()
        fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)
        with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
            if isinstance(result, dict):
                for sheet_name, df_sheet in result.items():
                    if df_sheet is not None and not df_sheet.empty:
                        df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                result.to_excel(writer, sheet_name='统计报表', index=False)
            # 应用样式（合并单元格、边框等）
            apply_excel_style(writer.book)
        self.current_report_path = temp_path
        self.download_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        QMessageBox.information(self, "成功", "报表已生成，点击「下载报表」保存文件")

    def on_generate_error(self, error_msg):
        self.progress.close()
        self.generate_btn.setEnabled(True)
        QMessageBox.critical(self, "生成报表失败", error_msg)