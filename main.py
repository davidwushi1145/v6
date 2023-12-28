from flask import Flask, request, send_file
import pm4py.vis
from pm4py.objects.log.importer.xes import importer as xes_importer
import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.discovery.alpha import algorithm as alpha_miner
from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
import os
from flask_cors import CORS  # 导入Flask-CORS


def import_event_log(file_path, file_format):
    if file_format == 'xes':
        log = xes_importer.apply(file_path)
    elif file_format == 'csv':
        dataframe = pd.read_csv(file_path)
        log = log_converter.apply(dataframe, variant=log_converter.Variants.TO_EVENT_LOG)
    else:
        raise ValueError("Unsupported file format. Please use 'csv' or 'xes'.")
    return log


# 定义一个函数来选择并应用挖掘算法
def apply_mining_algorithm(log, algorithm_name):
    if algorithm_name == 'alpha':
        net, initial_marking, final_marking = alpha_miner.apply(log)
    elif algorithm_name == 'heuristic':
        net, initial_marking, final_marking = heuristics_miner.apply(log)
    else:
        raise ValueError("Unsupported algorithm. Please use 'alpha' or 'heuristic'.")
    return net, initial_marking, final_marking


# 定义一个函数来可视化 Petri 网
def visualize_petri_net(net, initial_marking, final_marking):
    pm4py.vis.view_petri_net(net, initial_marking, final_marking)
    output_file_path = os.path.join('outputs', 'petri_net.png')
    pm4py.vis.save_vis_petri_net(net, initial_marking, final_marking, output_file_path)


app = Flask(__name__)
CORS(app)  # 设置跨域


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    algorithm_name = request.form.get('algorithm_name')
    file_format = file.filename.split('.')[-1]

    if file_format not in ['xes', 'csv']:
        return "Unsupported file format. Please use 'csv' or 'xes'.", 400

    if algorithm_name not in ['alpha', 'heuristic']:
        return "Unsupported algorithm. Please use 'alpha' or 'heuristic'.", 400

    file_path = os.path.join('uploads', file.filename)
    file.save(file_path)

    log = import_event_log(file_path, file_format)
    net, initial_marking, final_marking = apply_mining_algorithm(log, algorithm_name)
    output_file_path = os.path.join('outputs', file.filename + '.png')
    pm4py.vis.save_vis_petri_net(net, initial_marking, final_marking, output_file_path)

    return send_file(output_file_path, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True, port=1145)
