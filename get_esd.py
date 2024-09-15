# pan.ai-hobbyist.com 資料集格式中 lab 收集為 esd.list

import os
import argparse

def get_esd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, required=True, help='data 資料夾下的資料集名稱')
    parser.add_argument('--lang', type=str, required=True, help='語言 JP / ZH')
    args = parser.parse_args()
    dataset_name = args.name
    dataset_lang = args.lang
    
    esd = []
    path = f'data/{dataset_name}/raw/'
    total = os.listdir(path)
    now = 1
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.lab'):
                esd_row = ''
                this_lab_path = os.path.join(root, file)
                with open(this_lab_path, 'r', encoding='utf-8') as f:
                    esd_row = f.read()
                esd_row = f"{this_lab_path.replace('.lab', 'wav')}|{dataset_name}|{dataset_lang}|{esd_row}"
                esd.append(esd_row)
                print(f'[{now}/{len(total)}] {this_lab_path} done')
                now += 1
    print(f'共 {len(esd)} 筆資料')
    
    with open(f'data/{dataset_name}/esd.list', 'w', encoding='utf-8') as f:
        for item in esd:
            f.write("%s\n" % item)
    print('esd.list 已產生')

if __name__ == '__main__':
    get_esd()