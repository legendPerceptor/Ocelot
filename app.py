from tkinter import *
from tkinter import ttk
import yaml
import globus_utils
import os
import globus_sdk
import pickle
from sklearn.tree import DecisionTreeRegressor
from sklearn import tree
from funcx import FuncXExecutor
from funcx_utils import list_dir, execute, build_mpi_sbatch_file, mpi_operation
from os import path
from enum import Enum



class SourceType(Enum):
    WORK_DIR = 1
    DATA_PATH = 2
    OUTPUT_PATH = 3


class OcelotApp:
    def __init__(self):
        self.window = Tk() # create window
        self.window.title("Ocelot's Data Transfer With Lossy Compression")
        self.globus_client_id = StringVar()
        self.sender_uuid = StringVar()
        self.receiver_uuid = StringVar()
        self.sender_funcx_id = StringVar()
        self.receiver_funcx_id = StringVar()
        self.sender_build_folder = StringVar()
        self.receiver_build_folder = StringVar()
        self.sender_dir = StringVar()
        self.receiver_dir = StringVar()
        self.error_bound = StringVar()
        self.config_path = StringVar()
        self.sz3_config_path = StringVar()
        self.dimensions = StringVar()
        # self.source_dir = StringVar()
        # self.dest_dir = StringVar()
        self.dataset_path = StringVar()
        self.num_of_nodes = StringVar()
        self.output_path = StringVar()
        self.output_filename = StringVar()
        self.selected_source_files = []
        self.selected_dest_files = []
        self.status = StringVar()
        self.status.set("Running")
        self.tc = None # The globus transfer client
        self.transfer_doc = None
        self.source_type = SourceType.WORK_DIR
        self.globus_token_filename = "globus_tokens.json"
        self.config_path.set("examples/config.yml")

    def find_info(self, node_id):
        info = [str(node_id), "36", "95.8", "13s", "0.001"]
        return info

    def on_list_sender_dir_button(self):
        dir = self.sender_dir.get()
        self.source_type = SourceType.WORK_DIR
        self.list_files_tool(dir, self.funcx_sender, self.source_file_listbox, self.source_file_label, self.selected_source_files, "Source Files (Work Dir) {num} files:")

    def on_list_receiver_dir_button(self):
        dir = self.receiver_dir.get()
        self.list_files_tool(dir, self.funcx_receiver, self.dest_file_listbox, self.dest_file_label, self.selected_dest_files, "Destination Files (Work Dir) {num} files:")
    
    def on_list_data_button(self):
        dir = self.dataset_path.get()
        self.source_type = SourceType.DATA_PATH
        self.list_files_tool(dir, self.funcx_sender, self.source_file_listbox, self.source_file_label, self.selected_source_files, "Source Files (Data Path) {num} files:")
        
    def on_list_output_button(self):
        dir = path.join(self.sender_dir.get(), self.output_path.get())
        self.source_type = SourceType.OUTPUT_PATH
        self.list_files_tool(dir, self.funcx_sender, self.source_file_listbox, self.source_file_label, self.selected_source_files, "Source Files (Output Path) {num} files:")
    

    def list_files_callback(self, future, listbox, file_label, selected_files, label_content):
        try:
            result = future.result()
        except Exception as e:
            print(e)
            self.status.set("Error: Cannot list directory")
            self.status_label.configure(foreground='red')
            return
        file_label.configure(text=label_content.format(num=len(result)))
        listbox.delete(0, END)
        selected_files.clear()
        for file in result:
            listbox.insert(END, file)
        self.status.set("List Files Done")
        self.status_label.configure(foreground='green')

    def list_files_tool(self, dir, funcx_agent, listbox, file_label, selected_files, label_content):
        future = funcx_agent.submit(list_dir, dir)
        future.add_done_callback(lambda f: self.list_files_callback(f, listbox, file_label, selected_files, label_content))
        self.status.set("Listing files...")
        self.status_label.configure(foreground='yellow')

    def on_aunthenticate_button(self):
        # TODO: The Bebop machine stil hasn't updated to the new Globus Auth API
        # collections = [self.sender_uuid.get(), self.receiver_uuid.get()]
        collections = [self.sender_uuid.get()]
        cwd = os.getcwd()
        globus_client_id = self.globus_client_id.get().strip()
        print('globus client id:',globus_client_id)
        try:
            self.globus_authorizer = globus_utils.get_proxystore_authorizer(globus_client_id, self.globus_token_filename, cwd)
            # self.globus_authorizer = globus_utils.get_one_time_authorizer(globus_client_id, collections=collections)
            self.tc = globus_sdk.TransferClient(authorizer=self.globus_authorizer)
        except globus_utils.GlobusAuthFileError:
            print(
                'Performing authentication for the ProxyStore Globus Native app.',
            )
            globus_utils.proxystore_authenticate(
                client_id=globus_client_id,
                token_file_name=self.globus_token_filename,
                proxystore_dir=cwd,
                collections=collections,
            )
            self.globus_authorizer = globus_utils.get_proxystore_authorizer(globus_client_id, self.globus_token_filename, cwd)
            self.tc = globus_sdk.TransferClient(authorizer=self.globus_authorizer)
            print('Globus authorization complete.')
        else:
            print(
                'Globus authorization is already completed. To re-authenticate, '
                'delete your tokens (proxystore-globus-auth --delete) and try '
                'again.',
            )
        self.status.set("Globus Auth Done")
        self.status_label.configure(foreground='green')
        

    def on_load_config_button(self):
        config_path = self.config_path.get()
        with open(config_path, 'r') as file:
            try:
                self.config = yaml.safe_load(file)
                # print(self.config)
            except yaml.YAMLError as exc:
                print(exc)
                self.status.set("Error: Config file cannot be loaded")
                self.status_label.configure(foreground='red')
            
        try:
            sender = self.config['globus']['sender']
            receiver = self.config['globus']['receiver']
            self.sender = sender
            self.receiver = receiver
            self.sender_funcx_id.set(self.config[sender]['funcx_id'])
            self.receiver_funcx_id.set(self.config[receiver]['funcx_id'])
            self.sender_uuid.set(self.config[sender]['uuid'])
            self.receiver_uuid.set(self.config[receiver]['uuid'])
            self.sender_dir.set(self.config[sender]['cwd'])
            self.receiver_dir.set(self.config[receiver]['cwd'])
            self.sender_build_folder.set(self.config[sender]['build_folder'])
            self.receiver_build_folder.set(self.config[receiver]['build_folder'])
            self.globus_client_id.set(self.config['globus']['client_id'])
            self.sz3_config_path.set(self.config[sender]['job_config']['sz3_config'])
            self.dimensions.set(self.config[sender]['job_config']['dimension'])
            self.output_path.set(self.config[sender]['job_config']['output_path'])
            self.output_filename.set(self.config[sender]['job_config']['output_filename'])
            self.dataset_path.set(self.config[sender]['job_config']['dataset_path'])
            self.num_of_nodes.set(self.config[sender]['job_config']['nodes'])
            self.error_bound.set(self.config[sender]['job_config']['eb'])
        except KeyError as exc:
            print(exc)
            self.status.set("Error: Fields missing in config file")
            self.status_label.configure(foreground='red')
            return
        try:
            self.funcx_sender = FuncXExecutor(endpoint_id=self.sender_funcx_id.get())
            self.funcx_receiver = FuncXExecutor(endpoint_id=self.receiver_funcx_id.get())
        except Exception as exc:
            print(exc)
            self.status.set("Error: Cannot connect to funcx")
            self.status_label.configure(foreground='red')
            return

        if 'local' in self.config:
            local_config = self.config['local']
            self.PSNR_model = pickle.load(open(local_config['PSNR_model'], 'rb'))
            self.CPTime_model = pickle.load(open(local_config['CPTime_model'], 'rb'))
            self.CR_model = pickle.load(open(local_config['CR_model'], 'rb'))
        
        self.status.set("Config file is loaded")
        self.status_label.configure(foreground='green')
    
    def predict_done(self, future):
        df, stdout, stderr = future.result()
        df_selected = None
        if df is None:
            print(df)
            print(stdout)
            print(stderr)
        else:
            df_selected = df[['min', 'max', 'valueRange', 'avg_lorenzo', 'p0', 'ABS Error Bound', 'P0', 'predicted CR', 'entropy', 'quant_entropy']]
            print(df_selected)
            p_PSNR = self.PSNR_model.predict(df_selected)
            p_CPTime = self.CPTime_model.predict(df_selected)
            p_CR = self.CR_model.predict(df_selected)
            self.predicted_info_listbox.delete(0, END)
            self.predicted_info_listbox.insert(END, f"PSNR: {p_PSNR[0]}")
            self.predicted_info_listbox.insert(END, f"Compression Time: {p_CPTime[0]}")
            self.predicted_info_listbox.insert(END, f"Compression Ratio: {p_CR[0]}")
        self.status.set("Prediction is done")
        self.status_label.configure(foreground='green')

    def on_predict_selected_button(self):
        cwd = self.sender_dir.get()
        exe_file = path.join(self.sender_build_folder.get(), 'sz3_predict')
        csv_path = os.path.join(cwd, f"temporal.csv")
        compressed_file_path = os.path.join(cwd, self.output_path.get(), f"temporal.sz3")
        config_path = self.sz3_config_path.get()
        mode = "ABS"
        data_path = self.selected_source_files[0]
        dim = self.dimensions.get()
        eb = self.error_bound.get()
        command = f'{exe_file} -f {data_path} -d "{dim}" -m {mode} --eb {eb} -c {config_path} -o {csv_path}'
        # command = f'{exe_file} -f {data_path} -d "{dim}" -m {mode} --eb {eb} -c {config_path} -o {csv_path} -p {compressed_file_path}'
        print(command)
        future = self.funcx_sender.submit(execute, command, cwd, csv_path)
        future.add_done_callback(self.predict_done)
        self.status.set("Predicting...")
        self.status_label.configure(foreground='yellow')
        

    def on_compress_selected_button(self):
        cwd = self.sender_dir.get()
        exe_file = path.join(self.sender_build_folder.get(), 'sz3_compress')
        csv_path = os.path.join(cwd, f"temporal.csv")
        config_path = self.sz3_config_path.get()
        mode = "ABS"
        data_path = self.selected_source_files[0]
        filename = data_path.split('/')[-1]
        compressed_file_path = os.path.join(cwd, self.output_path.get(), f"{filename}.sz3")
        dim = self.dimensions.get()
        eb = self.error_bound.get()
        command = f'{exe_file} -f {data_path} -d "{dim}" -m {mode} --eb {eb} -c {config_path} -o {csv_path} -p {compressed_file_path}'
        print(command)
        self.compress_future = self.funcx_sender.submit(execute, command, cwd, csv_path)
        self.status.set("Single compress job is running")
        self.status_label.configure(foreground='yellow')
        self.compress_future.add_done_callback(self.compress_done)

    def on_compress_all_button(self):
        sender_config = self.config[self.sender]
        job_config = sender_config['job_config']
        output_file = path.join(self.sender_dir.get(), self.output_path.get(), self.output_filename.get())
        command = f"{path.join(self.sender_build_folder.get(), 'mpi_compress')} -q {self.dataset_path.get()} -p {output_file} -d '{self.dimensions.get()}' -e {self.error_bound.get()} -c {self.config_path.get()}"
        sbatch_file = build_mpi_sbatch_file(job_config, command)
        self.compress_future = self.funcx_sender.submit(mpi_operation, sbatch_file, self.sender_dir.get(), 'compress.sh')
        self.status.set("Parallel compress job is running")
        self.status_label.configure(foreground='yellow')
        # print(future.result())
        # pass
        self.compress_future.add_done_callback(self.compress_all_done)

    def compress_all_done(self, future):
        stdout, stderr = future.result()
        self.compress_future = None
        print(stdout)
        print(stderr)
        self.status.set("Parallel compress job is done")
        self.status_label.configure(foreground='green')
    
    def compress_done(self, future):
        _, stdout, stderr = future.result()
        self.compress_future = None
        print(stdout)
        print(stderr)
        self.status.set("Single compress job is done")
        self.status_label.configure(foreground='green')

    def on_check_compress_status_button(self):
        if self.compress_future is None:
            self.status.set("Error: No compress job is running")
            self.status_label.configure(foreground='red')
            return
        
        _, stdout, stderr = self.compress_future.result()
        self.compress_future = None
        print(stdout)
        print(stderr)
        self.status.set("Compress job is done")
        self.status_label.configure(foreground='green')
        # pass

    def on_transfer_selected_button(self):
        if self.tc is None:
            self.status.set("Error: Not authenticated")
            self.status_label.configure(foreground='red')
            return
        # create a Transfer task consisting of one or more items
        task_data = globus_sdk.TransferData(
            source_endpoint=self.sender_uuid.get(), destination_endpoint=self.receiver_uuid.get()
        )
        
        for i in range(len(self.selected_source_files)):
            file_name = self.selected_source_files[i].split('/')[-1]
            task_data.add_item(
                self.selected_source_files[i],  # source
                path.join(self.receiver_dir.get(), file_name),  # dest
            )
            print("transfering ", self.selected_source_files[i], " to ", path.join(self.receiver_dir.get(), file_name))
        # submit the task
        self.transfer_doc = self.tc.submit_transfer(task_data)
        self.on_check_transfer_status_button()

    def on_check_transfer_status_button(self):
        if self.transfer_doc is None:
            self.status.set("Error: No transfer task")
            self.status_label.configure(foreground='red')
            return
        
        task_id = self.transfer_doc["task_id"]
        task = self.tc.get_task(task_id)
        status = task['status']
        files = task['files']
        bytes_transferred = task['bytes_transferred']
        request_time = task['request_time']
        completion_time = task['completion_time']
        self.transform_performance_listbox.delete(0, END)
        self.transform_performance_listbox.insert(END, "Status: " + status)
        self.transform_performance_listbox.insert(END, "Bytes transferred: " + str(bytes_transferred))
        self.transform_performance_listbox.insert(END, "Request time: " + str(request_time))
        self.transform_performance_listbox.insert(END, "Completion time: " + str(completion_time))
        self.transform_performance_listbox.insert(END, "Files:" + str(files))
        if status == 'ACTIVE':
            self.status.set("Transfer task is running")
            self.status_label.configure(foreground='blue')
        elif status == 'SUCCEEDED':
            self.status.set("Transfer task is done")
            self.status_label.configure(foreground='green')


    def on_transfer_all_button(self):
        if self.tc is None:
            self.status.set("Error: Not authenticated")
            self.status_label.configure(foreground='red')
            return
        # create a Transfer task consisting of one or more items
        task_data = globus_sdk.TransferData(
            source_endpoint=self.sender_uuid.get(), destination_endpoint=self.receiver_uuid.get()
        )
        
        source_folder = path.join(self.sender_dir.get(), self.output_path.get())
        task_data.add_item(
            source_folder,  # source
            self.receiver_dir.get(),  # dest
            recursive=True
        )
        print("transfering ", source_folder, " to ", self.receiver_dir.get())
        # submit the task
        self.transfer_doc = self.tc.submit_transfer(task_data)
        self.on_check_transfer_status_button()

    def on_select_dest_files(self, event):
        w = event.widget
        if len(w.curselection()) == 0:
            return
        self.selected_dest_files = [w.get(int(index)) for index in w.curselection()]
        print("selected dest files: ", self.selected_dest_files)

    def on_select_source_files(self, event):
        w = event.widget
        if len(w.curselection()) == 0:
            return
        
        if self.source_type == SourceType.DATA_PATH:
            prefix = self.dataset_path.get()
        elif self.source_type == SourceType.OUTPUT_PATH:
            prefix = path.join(self.sender_dir.get(), self.output_path.get())
        elif self.source_type == SourceType.WORK_DIR:
            prefix = self.sender_dir.get()
        self.selected_source_files = [path.join(prefix, w.get(int(index))) for index in w.curselection()]
        print("selected source files: ", self.selected_source_files)

    
    def runGUI(self):
        
        window = self.window
        window.geometry("+300+300")

        tab_control = ttk.Notebook(window)
        tab_1 = ttk.Frame(tab_control)
        tab_control.add(tab_1, text='Parallel Compression')
        tab_control.pack(expand=1, fill='both')

        global_frame_row_ = 0 # global row counter for all frames
        top_frame = Frame(tab_1)
        top_frame.grid(row=global_frame_row_, column=0, sticky=W)

        global_font_ = ("Helvetica", 16, "bold")

        local_row_ = 0 # local row counter inside each frame

        client_id_label = Label(top_frame, text="Globus Client ID:", font=global_font_)
        client_id_label.grid(row=local_row_, column=0, sticky=W)
        client_id_text_field = Entry(top_frame, width=30, textvariable=self.globus_client_id)
        client_id_text_field.grid(row=local_row_, column=1, sticky=W)

        local_row_ += 1

        sender_funcx_id_label = Label(top_frame, text="Sender FuncX ID:", font=global_font_)
        sender_funcx_id_label.grid(row=local_row_, column=0, sticky=W)
        sender_funcx_id_text_field = Entry(top_frame, width=30, textvariable=self.sender_funcx_id)
        sender_funcx_id_text_field.grid(row=local_row_, column=1, sticky=W)

        local_row_ += 1

        receiver_funcx_id_label = Label(top_frame, text="Receiver FuncX ID:", font=global_font_)
        receiver_funcx_id_label.grid(row=local_row_, column=0, sticky=W)
        receiver_funcx_id_text_field = Entry(top_frame, width=30, textvariable=self.receiver_funcx_id)
        receiver_funcx_id_text_field.grid(row=local_row_, column=1, sticky=W)

        local_row_ += 1

        sender_uuid_label = Label(top_frame, text="Sender UUID:", font=global_font_)
        sender_uuid_label.grid(row=local_row_, column=0, sticky=W)
        sender_uuid_text_field = Entry(top_frame, width=30, textvariable=self.sender_uuid)
        sender_uuid_text_field.grid(row=local_row_, column=1, sticky=W)

        local_row_ += 1

        receiver_uuid_label = Label(top_frame, text="Receiver UUID:", font=global_font_)
        receiver_uuid_label.grid(row=local_row_, column=0, sticky=W)
        receiver_uuid_text_field = Entry(top_frame, width=30, textvariable=self.receiver_uuid)
        receiver_uuid_text_field.grid(row=local_row_, column=1, sticky=W)

        authenticate_button = Button(top_frame, text="Authenticate", font=global_font_, width=10, command=self.on_aunthenticate_button)
        authenticate_button.grid(row=local_row_, column=2, sticky=W)

        local_row_ += 1

        source_dir_label = Label(top_frame, text="Source Work Directory:", font=global_font_)
        source_dir_label.grid(row=local_row_, column=0, sticky=W)
        source_dir_text_field = Entry(top_frame, width=30, textvariable=self.sender_dir)
        source_dir_text_field.grid(row=local_row_, column=1, sticky=W)

        read_dir_source_button = Button(top_frame, text="List Source", font=global_font_, width=10, command=self.on_list_sender_dir_button)
        read_dir_source_button.grid(row=local_row_, column=2, sticky=W)

        local_row_ += 1

        dest_dir_label = Label(top_frame, text="Destination Work Directory:", font=global_font_)
        dest_dir_label.grid(row=local_row_, column=0, sticky=W)
        dest_dir_text_field = Entry(top_frame, width=30, textvariable=self.receiver_dir)
        dest_dir_text_field.grid(row=local_row_, column=1, sticky=W)

        read_dir_dest_button = Button(top_frame, text="List Dest", font=global_font_, width=10, command=self.on_list_receiver_dir_button)
        read_dir_dest_button.grid(row=local_row_, column=2, sticky=W)

        local_row_ += 1

        config_label = Label(top_frame, text="Config Path:", font=global_font_ )
        config_label.grid(row=local_row_, column=0, sticky=W)
        config_path_text_field = Entry(top_frame, width=30, textvariable=self.config_path)
        config_path_text_field.grid(row=local_row_, column=1, sticky=W)

        load_config_button = Button(top_frame, text="Load Config", font=global_font_, command=self.on_load_config_button)
        load_config_button.grid(row=local_row_, column=2, sticky=W)


        # status frame
        status_frame = LabelFrame(tab_1, text="Status", font=global_font_)
        status_frame.grid(row=global_frame_row_, column=1, sticky=W)
        self.status_label = Label(status_frame, textvariable=self.status, font=global_font_)
        self.status_label.grid(row=0, column=0, sticky=W)

        # The compression settings
        global_frame_row_ += 1

        compression_settings_frame = LabelFrame(tab_1, text="Compression Settings", font=global_font_)
        compression_settings_frame.grid(row=global_frame_row_, column=0, sticky=W)

        sz3_config_label = Label(compression_settings_frame, text="SZ3 Config Path:", font=global_font_)
        sz3_config_label.grid(row=0, column=0, sticky=W)
        sz3_config_text_field = Entry(compression_settings_frame, width=30, textvariable=self.sz3_config_path)
        sz3_config_text_field.grid(row=0, column=1, sticky=W)


        dimensions_label = Label(compression_settings_frame, text="Dimensions:", font=global_font_)
        dimensions_label.grid(row=0, column=2, sticky=W)
        dimensions_text_field = Entry(compression_settings_frame, width=10, textvariable=self.dimensions)
        dimensions_text_field.grid(row=0, column=3, sticky=W)

        output_path_label = Label(compression_settings_frame, text="Output Path:", font=global_font_)
        output_path_label.grid(row=1, column=0, sticky=W)
        output_path_text_field = Entry(compression_settings_frame, width=30, textvariable=self.output_path)
        output_path_text_field.grid(row=1, column=1, sticky=W)

        output_file_name_label = Label(compression_settings_frame, text="Output File Name:", font=global_font_)
        output_file_name_label.grid(row=1, column=2, sticky=W)
        output_file_name_text_field = Entry(compression_settings_frame, width=10, textvariable=self.output_filename)
        output_file_name_text_field.grid(row=1, column=3, sticky=W)

        dataset_path_label = Label(compression_settings_frame, text="Dataset Path:", font=global_font_)
        dataset_path_label.grid(row=2, column=0, sticky=W)
        dataset_path_text_field = Entry(compression_settings_frame, width=30, textvariable=self.dataset_path)
        dataset_path_text_field.grid(row=2, column=1, sticky=W)

        num_of_nodes_label = Label(compression_settings_frame, text="Number of Nodes:", font=global_font_)
        num_of_nodes_label.grid(row=2, column=2, sticky=W)
        num_of_nodes_text_field = Entry(compression_settings_frame, width=10, textvariable=self.num_of_nodes)
        num_of_nodes_text_field.grid(row=2, column=3, sticky=W)


        error_bound_label = Label(compression_settings_frame, text="Error Bound:", font=global_font_)
        error_bound_label.grid(row=3, column=0, sticky=W)
        error_bound_text_field = Entry(compression_settings_frame, width=10, textvariable=self.error_bound)
        error_bound_text_field.grid(row=3, column=1, sticky=W)

        list_datapath_button = Button(compression_settings_frame, text="List Datapath", font=global_font_, width=10, command=self.on_list_data_button)
        list_datapath_button.grid(row=3, column=2, sticky=W)

        list_outputpath_button = Button(compression_settings_frame, text="List Output", font=global_font_, width=10, command=self.on_list_output_button)
        list_outputpath_button.grid(row=3, column=3, sticky=E)

        # The button line of compression bottom
        global_frame_row_ += 1
        final_line_compression_frame = Frame(tab_1)
        final_line_compression_frame.grid(row=global_frame_row_, column=0, sticky=W)

        predict_button = Button(final_line_compression_frame, text="Predict Selected", font=global_font_, command=self.on_predict_selected_button)
        predict_button.grid(row=0, column=0, sticky=W)

        compress_button = Button(final_line_compression_frame, text="Compress Selected", font=global_font_, command=self.on_compress_selected_button)
        compress_button.grid(row=0, column=1, sticky=W)

        compress_all_button = Button(final_line_compression_frame, text="Compress All", font=global_font_, command=self.on_compress_all_button)
        compress_all_button.grid(row=0, column=2, sticky=W)

        transfer_selected_button = Button(final_line_compression_frame, text="Transfer Selected", font=global_font_, command=self.on_transfer_selected_button)
        transfer_selected_button.grid(row=0, column=3, sticky=W)

        transfer_all_button = Button(final_line_compression_frame, text="Transfer All", font=global_font_, command=self.on_transfer_all_button)
        transfer_all_button.grid(row=0, column=4, sticky=W)


        global_frame_row_ += 1
        button_line2_compression_frame = Frame(tab_1)
        button_line2_compression_frame.grid(row=global_frame_row_, column=0, sticky=W)

        check_compression_status_button = Button(button_line2_compression_frame, text="Check Compression Status", font=global_font_)
        check_compression_status_button.grid(row=0, column=0, sticky=W)

        check_transfer_status_button = Button(button_line2_compression_frame, text="Check Transfer Status", font=global_font_, command=self.on_check_transfer_status_button)
        check_transfer_status_button.grid(row=0, column=1, sticky=W)

        # The bottom frame
        global_frame_row_ += 1
        bottom_frame = Frame(tab_1)
        bottom_frame.grid(row=global_frame_row_, column=0, sticky=W)


        local_row_ = 0

        self.source_file_label = Label(bottom_frame, text="Source Files:", font=global_font_)
        self.source_file_label.grid(row=local_row_, column=0, sticky=W)
        self.dest_file_label = Label(bottom_frame, text="Destination Files:", font=global_font_)
        self.dest_file_label.grid(row=local_row_, column=1, sticky=W)

        local_row_ += 1

        source_file_frame = Frame(bottom_frame)
        source_file_frame.grid(row=local_row_, column=0, sticky=N+S)

        source_file_scrollbar = Scrollbar(source_file_frame, orient="vertical")
        source_file_scrollbar.pack(side=RIGHT, fill=Y)

        self.source_file_listbox = Listbox(source_file_frame, width=50, yscrollcommand=source_file_scrollbar.set, font=("Helvetica", 12), selectmode = "single")
        self.source_file_listbox.pack(expand=True, fill=Y)

        self.source_file_listbox.bind('<<ListboxSelect>>', self.on_select_source_files)

        source_file_scrollbar.config(command=self.source_file_listbox.yview)

        dest_file_frame = Frame(bottom_frame)
        dest_file_frame.grid(row=local_row_, column=1, sticky=N+S)

        dest_file_scrollbar = Scrollbar(dest_file_frame, orient="vertical")
        dest_file_scrollbar.pack(side=RIGHT, fill=Y)

        self.dest_file_listbox = Listbox(dest_file_frame, width=50, yscrollcommand=dest_file_scrollbar.set, font=("Helvetica", 12), selectmode = "single")
        self.dest_file_listbox.pack(expand=True, fill=Y)

        self.dest_file_listbox.bind('<<ListboxSelect>>', self.on_select_dest_files)

        dest_file_scrollbar.config(command=self.dest_file_listbox.yview)

        # Predicted Info Frame
        global_frame_row_+=1
        predicted_info_frame = Frame(tab_1)
        predicted_info_frame.grid(row=global_frame_row_, column=0, sticky=W)

        local_row_ = 0

        predicted_info_label = Label(predicted_info_frame, text="Source Predicted Info:", font=("Helvetica", 16,"bold"))
        predicted_info_label.grid(row=local_row_, column=0, sticky=W)

        transfer_performance_label = Label(predicted_info_frame, text="Transfer Performance:", font=("Helvetica", 16,"bold"))
        transfer_performance_label.grid(row=local_row_, column=1, sticky=W)

        local_row_ += 1
        self.predicted_info_listbox = Listbox(predicted_info_frame, height=5, width=50, font=("Helvetica", 12))
        self.predicted_info_listbox.grid(row=local_row_, column=0, sticky=W)

        self.transform_performance_listbox = Listbox(predicted_info_frame, height=5, width=50, font=("Helvetica", 12))
        self.transform_performance_listbox.grid(row=local_row_, column=1, sticky=W)


        # for x in range(100):
        #     source_file_listbox.insert(END, x)
        #     dest_file_listbox.insert(END, x)

        window.mainloop()




if __name__ == "__main__":
    app = OcelotApp()
    app.runGUI()

