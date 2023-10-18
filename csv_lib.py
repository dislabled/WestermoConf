#!/usr/bin/env python3
# coding=utf-8
"""Handle all CSV Related stuff."""
from csv import DictReader, DictWriter


class ConfigFile:
    """Read and write CSV configfile."""

    def __init__(self) -> None:
        """Initialize class."""
        pass

    def read_config(self, file: str) -> list:
        """
        Read CSV file and output dictionary.

        Header - Cabinet,AP,SW,IOG,MBB,DIPB,MBR,DIPR,IBC IP address,
                 Switch IP address,Position,MAC M,MAC R
        input:
            csvfile (str)
        Outputs:
            parsed dictionary(list)
        """
        with open(file, "r") as f:
            config = list(DictReader(f, delimiter=",", quotechar='"'))
        return config

    def write_config(self, file: str, cabinet: str, mac: str, main: bool) -> None:
        """
        Write the MAC address to the csv file.

        input:
            file(str)
            cabinet(str) row to change
            mac(str) MAC to add row
            main(bool) Main or Reserve Mac to add
        """
        with open(file, "r+") as f:
            csvobject = DictReader(f, delimiter=",", quotechar='"')
            if csvobject.fieldnames is not None:
                fieldnames = csvobject.fieldnames
            else:
                fieldnames = ""
            csvlist = list(csvobject)
            for row in csvlist:
                if row["Cabinet"] == cabinet:
                    if main:
                        row["MAC M"] = mac
                    else:
                        row["MAC R"] = mac
            f.seek(0)
            data = DictWriter(f, delimiter=",", quotechar='"', fieldnames=fieldnames)
            data.writeheader()
            data.writerows(csvlist)


if __name__ == "__main__":
    pass
