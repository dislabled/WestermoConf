#!/usr/bin/env python3
# coding=utf-8
"""
A GUI configurator for Westermo weos switches
"""
import sys
import tkinter as tk
from tkinter import BooleanVar, messagebox as mb
from tkinter import filedialog as fd
from tkinter import ttk
from westermo_ser_lib import Westermo
from csv_lib import ConfigFile


class WestermoGUI(tk.Tk):
    """ Root window for Westermo configurator
    """
    def __init__(self, *args, **kwargs) -> None:
        tk.Tk.__init__(self, *args, **kwargs)
        self.wm_title('Westermo Configurator')
        self.resizable(False, False)
        # self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<Escape>", lambda _: self.show_frame(MainPage))
        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)

        self.frames = {}
        for F in (MainPage, AutoConf, LogView):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(MainPage)

    def show_frame(self, cont):
        """ Method to raise frames
        """
        self.config(cursor='watch')
        frame = self.frames[cont]
        frame.tkraise()
        frame.refresh()
        self.config(cursor='')


class MainPage(tk.Frame):
    """ Main Frame
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.frame0 = tk.Frame(self)    # Hostname etc
        self.frame0.grid(row=0, column=0, sticky='nw')
        self.frame1 = tk.Frame(self)    # Ports
        self.frame1.grid(row=0, column=2, sticky='n')
        self.frame2 = tk.Frame(self)    # Buttons
        self.frame2.grid(row=1, column=0,  sticky='s', padx=3, pady=5)

        self.alobjports = [BooleanVar(), BooleanVar(), BooleanVar(),
                           BooleanVar(), BooleanVar(), BooleanVar(),
                           BooleanVar(), BooleanVar(),
                           BooleanVar(), BooleanVar()]

        tk.Label(self.frame0, text='Name: ').grid(row=0, column=0,
                                                sticky='w', padx=5, pady=1)
        self.swname = tk.Entry(self.frame0, width=24)
        self.swname.grid(row=0, column=1, sticky='w', padx=5, pady=1)
        self.upd_btn1 = tk.Button(self.frame0, text="Update", command=self.upd_name)
        self.upd_btn1.grid(row=0, column=2)
        tk.Label(self.frame0, text='Location: ').grid(row=1, column=0,
                                                sticky='w', padx=5, pady=1)
        self.swloc = tk.Entry(self.frame0, width=24)
        self.swloc.grid(row=1, column=1, sticky='w', padx=5, pady=1)
        self.upd_btn2 = tk.Button(self.frame0, text="Update", command=self.upd_loc)
        self.upd_btn2.grid(row=1, column=2)
        tk.Label(self.frame0, text='Description: ').grid(row=2, column=0,
                                                sticky='w', padx=5, pady=1)
        self.swdesc = tk.Text(self.frame0, height=1, width=24)
        self.swdesc.grid(row=2, column=1, sticky='w', padx=5, pady=1)
        tk.Label(self.frame0, text='MAC addr: ').grid(row=3, column=0,
                                                sticky='w', padx=5, pady=1)
        self.swmac = tk.Text(self.frame0, height=1, width=17)
        self.swmac.grid(row=3, column=1, sticky='w', padx=5, pady=1)
        tk.Label(self.frame0, text='Uptime: ').grid(row=4, column=0,
                                                sticky='w', padx=5, pady=1)
        self.swupt = tk.Text(self.frame0, height=1, width=12)
        self.swupt.grid(row=4, column=1, sticky='w', padx=5, pady=1)
        tk.Label(self.frame0, text='Model ver: ').grid(row=5, column=0,
                                                sticky='w', padx=5, pady=1)
        self.swver = tk.Text(self.frame0, height=1, width=24)
        self.swver.grid(row=5, column=1, sticky='w', padx=5, pady=1)
        tk.Label(self.frame0, text='FW ver: ').grid(row=6, column=0,
                                                sticky='w', padx=5, pady=1)
        self.swswv = tk.Text(self.frame0, height=1, width=24)
        self.swswv.grid(row=6, column=1, sticky='w', padx=5, pady=1)
        tk.Label(self.frame0, text='IP address: ').grid(row=7, column=0,
                                                sticky='w', padx=5, pady=1)
        self.swip = tk.Entry(self.frame0, width=24)
        self.swip.grid(row=7, column=1, sticky='w', padx=5, pady=1)
        self.upd_btn3 = tk.Button(self.frame0, text="Update", command=self.upd_ip)
        self.upd_btn3.grid(row=7, column=2)

        tk.Label(self.frame1, text='Ports:').grid(row=0, column=0, columnspan=4)
        self.port_1 = tk.Checkbutton(self.frame1, text='1',
                                     variable=self.alobjports[0],
                                     command=lambda: self.p_refresh())
        self.port_1.grid(row=5, column=1, padx=0)
        self.port_2 = tk.Checkbutton(self.frame1, text='2',
                                     variable=self.alobjports[1],
                command=lambda: self.p_refresh())
        self.port_2.grid(row=5, column=3, padx=0)
        self.port_3 = tk.Checkbutton(self.frame1, text='3',
                                     variable=self.alobjports[2],
                command=lambda: self.p_refresh())
        self.port_3.grid(row=4, column=1, padx=0)
        self.port_4 = tk.Checkbutton(self.frame1, text='4',
                                     variable=self.alobjports[3],
                command=lambda: self.p_refresh())
        self.port_4.grid(row=4, column=3, padx=0)
        self.port_5 = tk.Checkbutton(self.frame1, text='5',
                                     variable=self.alobjports[4],
                command=lambda: self.p_refresh())
        self.port_5.grid(row=3, column=1, padx=0)
        self.port_6 = tk.Checkbutton(self.frame1, text='6',
                                     variable=self.alobjports[5],
                command=lambda: self.p_refresh())
        self.port_6.grid(row=3, column=3, padx=0)
        self.port_7 = tk.Checkbutton(self.frame1, text='7',
                                     variable=self.alobjports[6],
                command=lambda: self.p_refresh())
        self.port_7.grid(row=2, columnspan=4, padx=0)
        self.port_8 = tk.Checkbutton(self.frame1, text='8',
                                     variable=self.alobjports[7],
                command=lambda: self.p_refresh())
        self.port_8.grid(row=1, columnspan=4, padx=0)
        self.port_9 = tk.Checkbutton(self.frame1, text='9',
                                     variable=self.alobjports[8],
                                     command=lambda: self.p_refresh())
        self.port_9.grid(row=1, columnspan=4, padx=0)
        self.port_10 = tk.Checkbutton(self.frame1, text='10',
                                      variable=self.alobjports[9],
                                      command=lambda: self.p_refresh())
        self.port_10.grid(row=1, columnspan=4, padx=0)

        button1 = tk.Button(self.frame2, text="download config",
                            command=self.download_config)
        button1.grid(row=0, column=0)
        button3 = tk.Button(self.frame2, text="auto configure",
                            command=lambda: controller.show_frame(AutoConf))
        button3.grid(row=0, column=2)
        button4 = tk.Button(self.frame2, text="factory reset",
                            command=self.factory_reset)
        button4.grid(row=1, column=0)
        button5 = tk.Button(self.frame2, text="alarm log",
                            command=lambda: controller.show_frame(LogView))
        button5.grid(row=1, column=1)
        button6 = tk.Button(self.frame2, text="copy ram2rom",
                            command=self.apply)
        button6.grid(row=1, column=2)


    def p_refresh(self):
        """ Refresh port values
        """
        self.config(cursor='watch')
        templist = []
        for port in self.alobjports:
            templist.append(port.get())
        switch.set_alarm(templist)
        self.refresh()

    def portcolor(self) -> list:
        """ Set background colors of connected ports
        """
        pcol = ['', '', '', '', '', '', '', '', '', '', '']
        for count, port in enumerate(self.stintports):
            if port:
                pcol[count] = '#000fff000' # Green
            else:
                pcol[count] = '#D9D9D9' # Same as background
        return pcol

    def factory_reset(self):
        """ Factory reset the switch
        """
        self.config(cursor='watch')
        if mb.askokcancel(title='Warning', message='Do you wish to proceed?'):
            switch.factory_conf()
            sys.exit(0)

    def download_config(self):
        """ Download the switch running config
        """
        initial_file = switch.get_sysinfo()[0]
        filename = fd.asksaveasfilename(defaultextension='.ini',
                                        initialdir='./site/configs/',
                                        initialfile=initial_file)
        if filename != ():
            contents = switch.save_config()
            with open(filename, "w") as config:
                config.write(contents)

    def apply(self):
        """ Save the running config to startup config
        """
        result = switch.save_run2startup()
        print(result)
        if result:
            mb.showinfo(message= 'Success')
        else:
            mb.showerror(title='Error', message='Something went wrong')

    def upd_name(self):
        """ Write the new hostname
        """
        switch.set_hostname(self.swname.get())

    def upd_loc(self):
        """ Write the new location
        """
        switch.set_location(self.swloc.get())

    def upd_ip(self):
        """ Write the new IP address
        """
        switch.set_mgmt_ip(self.swip.get())

    def refresh(self) -> None:
        """ Read and refresh values on screen
        """
        # Read new values
        self.system = switch.get_sysinfo()
        self.uptime = switch.get_uptime()
        self.portlist: list[dict[str, str]] = switch.get_ports()
        self.alintports: list[bool] = []
        self.stintports: list[bool] = []
        for val in self.portlist:
            self.alintports.append(bool(val['alarm']))
            self.stintports.append(bool(val['link']))
        self.mgmt_ips = switch.get_mgmt_ip()
        self.mgmt_ip = ''
        for val in self.mgmt_ips:
            if val['iface_name'] == 'vlan1':
                try:
                    self.mgmt_ip = val['secondary_ip']
                except KeyError:
                    self.mgmt_ip = ''
        print(self.mgmt_ip)

        for num, val in enumerate(self.alintports):
            if val:
                self.alobjports[num].set(True)
        # Delete old values
        self.swname.delete(0, tk.END)
        self.swloc.delete(0, tk.END)
        self.swdesc.delete(1.0, tk.END)
        self.swmac.config(bg='#D9D9D9', relief=tk.FLAT, state=tk.NORMAL)
        self.swmac.delete(1.0, tk.END)
        self.swupt.config(bg='#D9D9D9', relief=tk.FLAT, state=tk.NORMAL)
        self.swupt.delete(1.0, tk.END)
        self.swver.config(bg='#D9D9D9', relief=tk.FLAT, state=tk.NORMAL)
        self.swver.delete(1.0, tk.END)
        self.swswv.config(bg='#D9D9D9', relief=tk.FLAT, state=tk.NORMAL)
        self.swswv.delete(1.0, tk.END)
        self.swip.delete(0, tk.END)
        # Insert new values
        self.swname.insert(tk.END, self.system['system_name'])
        try:
            self.swloc.insert(tk.END, self.system['system_location'])
        except KeyError:
            self.swloc.insert(tk.END, '')

        self.swdesc.insert(tk.END, self.system['hw_model'])
        self.swmac.insert(tk.END, self.system['system_mac'])
        self.swmac.config(bg='#D9D9D9', relief=tk.FLAT, state=tk.DISABLED)
        self.swupt.insert(tk.END, self.uptime)
        self.swupt.config(bg='#D9D9D9', relief=tk.FLAT, state=tk.DISABLED)
        self.swver.insert(tk.END, self.system['hw_family'])
        self.swver.config(bg='#D9D9D9', relief=tk.FLAT, state=tk.DISABLED)
        self.swswv.insert(tk.END, self.system['system_firmware'])
        self.swswv.config(bg='#D9D9D9', relief=tk.FLAT, state=tk.DISABLED)
        self.swip.insert(tk.END, self.mgmt_ip)
        self.pcol = self.portcolor()
        self.port_1.config(background=self.pcol[0])
        self.port_2.config(background=self.pcol[1])
        self.port_3.config(background=self.pcol[2])
        self.port_4.config(background=self.pcol[3])
        self.port_5.config(background=self.pcol[4])
        self.port_6.config(background=self.pcol[5])
        self.port_7.config(background=self.pcol[6])
        self.port_8.config(background=self.pcol[7])
        self.port_9.config(background=self.pcol[8])
        self.port_10.config(background=self.pcol[9])
        self.config(cursor='')

class AutoConf(tk.Frame):
    """ Devicewindow GUI for Westermo configurator
    """

    def __init__(self, parent, controller) -> None:
        tk.Frame.__init__(self, parent)
        self.config_file = ConfigFile()
        self.file = ''
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.frame0 = tk.Frame(self) # Buttons
        self.frame0.grid(row=0, column=0, sticky='n')
        self.frame1 = tk.Frame(self) # Treeview
        self.frame1.grid(row=1, column=0, sticky='nsew')
        self.frame2 = tk.Frame(self) # Statusline
        self.frame2.grid(row=2, column=0, sticky='nsew')
        # Treeview
        self.columns = ('cab', 'sw_ip', 'loc')
        self.tree = ttk.Treeview(self.frame1, columns=self.columns,
                                 show='headings', height=30)
        self.tree.column('cab', width=150, anchor=tk.NW)
        self.tree.column('sw_ip', width=150, anchor=tk.NW)
        self.tree.column('loc', width=350, anchor=tk.NW)
        self.tree.heading('cab', text='Cabinet')
        self.tree.heading('sw_ip', text='Switch IP')
        self.tree.heading('loc', text='Location')
        self.tree.bind('<Double-1>', self.item_selected)
        self.scrollbar = ttk.Scrollbar(self.frame1, orient=tk.VERTICAL,
            command=self.tree.yview)
        self.scrollbar.pack(fill=tk.BOTH, expand=True, side="right")
        self.tree.pack(fill=tk.BOTH, expand=1)
        # Buttons
        self.swconf = tk.IntVar(value=0)
        self.swmainred = tk.IntVar(value=0)
        self.done_button = tk.Button(self.frame0, text="all switches",
            width=10, command=self.bswitch)
        self.done_button.pack(side='left')
        self.main_button = tk.Radiobutton(self.frame0, text="Main",
            variable=self.swmainred, indicatoron=False,
            value=0, width=8, command=self.refresh)
        self.main_button.pack(side='left')
        self.red_button = tk.Radiobutton(self.frame0, text="Red",
            variable=self.swmainred, indicatoron=False,
            value=1, width=8, command=self.refresh)
        self.red_button.pack(side='left')
        self.return_button = tk.Button(self.frame0, text="Return", width=10,
            command=lambda: controller.show_frame(MainPage))
        self.return_button.pack(side='left')

    def item_selected(self, event) -> None:
        """ get selected value and write config to switch
        """
        _ = event   # Hush some editor warnings
        config = self.tree.item(self.tree.focus())['values']
        ports = [0,0,0,0,0,0,0,0]
        for count, port in enumerate(switch.get_ports()):
            if port:
                ports[count] = 1
        if self.swmainred.get() == 0:
            main_reserve = 'M'
        else:
            main_reserve = 'R'
        message = (f'Hostname: {config[0] + main_reserve}\n'
                     f'Location: {config[2]}\n'
                     f'IP Address: {config[1]}\n'
                     f'Alarm on {ports}')
        if mb.askokcancel(title='Continue?', message=message):
            switch.set_hostname(config[0] + main_reserve)
            switch.set_location(config[2])
            switch.set_mgmt_ip(config[1])
            switch.set_alarm(ports)
            switch.save_run2startup()
            self.config_file.write_config(self.file, config[0],
                                    switch.get_sysinfo()[4],
                                    True if self.swmainred.get() ==  0 else False )
            self.refresh()

    def bswitch(self) -> None:
        """ On/Off switch
        """
        if self.swconf.get() == 0:
            self.done_button.configure(text='unconfigured')
            self.swconf.set(1)
        else:
            self.done_button.configure(text='all switches')
            self.swconf.set(0)
        self.refresh()

    def refresh(self) -> None:
        """ Refresh the values in the frame
        """
        if self.file == '':
            file = fd.askopenfilename(initialdir='./site/',
                                      filetypes=[('Comma Seperated files', '.csv')])
            if file != '':
                self.file = file

        for entry in self.tree.get_children():
            self.tree.delete(entry)
        csvlist = self.read_config(self.file)
        for entry in csvlist:
            self.tree.insert('', tk.END, values=list(entry))
        # Statusline
        total_count = len(self.tree.get_children())
        label = ttk.Label(self.frame2, text=f'Total objects: {total_count}')
        label.grid(row=0, column=0)

    def read_config(self, file:str) -> list:
        """ Read and parse CSV file according to buttons

            input:
                csvfile (str)
            Outputs:
                parsed list (list)
        """
        config = []
        csvconfig = self.config_file.read_config(file)
        for row in csvconfig:
            if row['SW'] == '1':
                # Not configured
                if self.swconf.get() == 0:
                    # Only Main
                    if self.swmainred.get() == 0:
                        config.append((row['Cabinet'], row['Switch IP address'],
                                       row['Position']))
                    # Only Reserve
                    else:
                        if row['DIPB'] != "":
                            config.append((row['Cabinet'], row['Switch IP address'],
                                           row['Position']))
                # Configured
                else:
                    # Only Main
                    if self.swmainred.get() == 0:
                        if row['DIPB'] != "" and row['MAC M'] == "":
                            config.append((row['Cabinet'], row['Switch IP address'],
                                           row['Position']))
                    # Only Reserve
                    else:
                        if row['DIPR'] != "" and row['MAC R'] == "":
                            config.append((row['Cabinet'], row['Switch IP address'],
                                           row['Position']))
        return config


class LogView(tk.Frame):
    """ Logviewer GUI for Westermo configurator
    """
    def __init__(self, parent, controller) -> None:
        tk.Frame.__init__(self, parent)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # Frame 0 BUTTONS:
        self.frame0 = tk.Frame(self)
        self.frame0.grid(row=0, column=0, sticky='n')
        self.clr_button = tk.Button(self.frame0, text="Clear Log",
                width=10, command=lambda: self.clearlog())
        self.return_button = tk.Button(self.frame0, text="Return",
                width=10, command=lambda: controller.show_frame(MainPage))
        # Frame 1 TEXTBOX:
        self.frame1 = tk.Frame(self)
        self.frame1.grid(row=1, column=0, sticky='nsew')
        self.scrollbar = ttk.Scrollbar(self.frame1, orient=tk.VERTICAL)
        self.logtext = tk.Text(self.frame1)

    def clearlog(self) -> None:
        """ Clear the Eventlog
        """
        self.config(cursor='watch')
        # switch.clear_eventlog()
        self.refresh()

    def refresh(self) -> None:
        """ Refresh the values in the frame
        """
        self.clr_button.pack(side='left')
        self.return_button.pack(side='left')
        self.config(cursor='watch')
        self.logtext.config(state=tk.NORMAL)
        self.logtext.delete(1.0, tk.END)
        # self.logtext.insert(tk.END, switch.get_eventlog())
        self.logtext.grid() #, padx=5, pady=1)
        self.logtext.config(state=tk.DISABLED)
        self.config(cursor='')


if __name__ == '__main__':
    SWITCH = {
        'host': '192.168.2.200',
        'auth_username': 'admin',
        'auth_password': 'westermo',
        'auth_strict_key': False,
        'platform': 'westermo_weos'
    }
    with Westermo(verbose=True, **SWITCH) as switch:
        start = WestermoGUI()
        start.mainloop()

