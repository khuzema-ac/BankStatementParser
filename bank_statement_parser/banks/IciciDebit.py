from datetime import date
from typing import List
import numpy as np
import pandas as pd
import bank_statement_parser.Bank as Bank
from bank_statement_parser.Transaction import Transaction


class IciciDebit(Bank):
    __id_bank = "ICICI-DEBIT"

    def getTransactions(self, filename: str) -> List[Transaction]:
        transactions: List[Transaction] = []
        df = self.getData(filename)
        self.validateDataframe(df)

        for index, row in df.iterrows():
            _checkNo = ""
            _duplicate = ""

            if row["Cheque Number"].strip() != "-":
                _checkNo = "CHQ: " + row["Cheque Number"].strip() + " "

            if row["Seq"] > 1:
                _duplicate = " (" + str(row["Seq"]) + ") "

            created_date = row["Transaction Date"]
            remarks = _checkNo + row["Transaction Remarks"].strip() + _duplicate
            amount = row["Deposit Amount (INR )"] - row["Withdrawal Amount (INR )"]
            transaction = Transaction(
                bank=self.__id_bank,
                created_date=created_date,
                remarks=remarks,
                amount=amount,
            )
            transactions.append(transaction)

        return transactions
    
    def getData(self, filename: str) -> pd.DataFrame:
        skip_rows = self.get_transaction_start(filename, ["date", "sr.no"])
        df_full = self.load_bank_statement(filename, skip_rows=skip_rows)
        df_filtered = df_full[df_full.iloc[:, 8].notna()]  # filter out empty rows
        new_header = df_filtered.iloc[0]  # grab the first row for the header
        df1 = df_filtered[1:]  # take the data less the header row
        df1.columns = new_header  # set the header row as the df header
        df = df1.copy()
        return df

    def validateDataframe(self, df):
        if "Transaction Date" not in df.columns:
            raise ValueError("Transaction Date not found")

        if "S No." not in df.columns:
            raise ValueError("S No. not found")

        if "Cheque Number" not in df.columns:
            raise ValueError("Cheque Number not found")

        if "Transaction Remarks" not in df.columns:
            raise ValueError("Transaction Remarks not found")

        if "Withdrawal Amount (INR )" not in df.columns:
            raise ValueError("Withdrawal Amount (INR ) not found")

        if "Deposit Amount (INR )" not in df.columns:
            raise ValueError("Deposit Amount (INR ) not found")

        df[["S No."]] = df[["S No."]].astype(int)
        df[["Withdrawal Amount (INR )", "Deposit Amount (INR )"]] = df[
            ["Withdrawal Amount (INR )", "Deposit Amount (INR )"]
        ].astype(float)
        df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], dayfirst=True)

        if df["S No."].max() != len(df):
            raise ValueError("No. of rows does not match")
        # to handle duplicate on same day
        df["Seq"] = (
            df.groupby(
                [
                    "Transaction Date",
                    "Cheque Number",
                    "Transaction Remarks",
                    "Withdrawal Amount (INR )",
                    "Deposit Amount (INR )",
                ]
            )
            .cumcount()
            .add(1)
        )
