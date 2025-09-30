import pandas as pd
import re
import requests
from pathlib import Path
import os
from time import sleep
import traceback

# ===== 路径处理 =====
script_dir = Path(__file__).parent  # 获取脚本所在目录
input_file = script_dir / "name.csv"  # 输入文件绝对路径
output_file = script_dir / "shenzhen_poi_data.csv"

# 验证输入文件存在
if not input_file.exists():
    raise FileNotFoundError(f"输入文件不存在：{input_file.resolve()}")


# ===== 经纬度获取 =====
def get_lng_lat(address, api_key):
    """根据地址获取经纬度"""
    url = f'https://restapi.amap.com/v3/geocode/geo?key={api_key}&address={address}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 检查HTTP错误
        data = response.json()
        
        print(f"API响应状态：{data.get('status', '未知')}, 结果数量：{data.get('count', 0)}")
        
        if data.get("status") == "1" and int(data.get("count", 0)) > 0:
            location = data["geocodes"][0]["location"]
            lng, lat = location.split(",")
            return float(lng), float(lat)
        else:
            print(f"高德API返回空数据或无结果：{address}")
            print(f"API返回信息：{data}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败：{str(e)}")
        return None, None
    except Exception as e:
        print(f"解析错误：{str(e)}")
        print(f"错误详情：{traceback.format_exc()}")
        return None, None


# ===== 主流程 =====
try:
    # 读取数据（支持Excel格式）
    try:
        # 首先尝试读取为Excel文件
        df = pd.read_excel(input_file)
    except Exception as excel_error:
        print(f"无法作为Excel文件读取：{excel_error}")
        try:
            # 尝试读取为CSV
            df = pd.read_csv(input_file, encoding="utf-8")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(input_file, encoding="gbk")
            except Exception as csv_error:
                print(f"也无法作为CSV文件读取：{csv_error}")
                raise Exception("无法识别文件格式，请确保文件是Excel或CSV格式")
    
    print(f"成功读取数据，共{len(df)}行")
    print(f"列名：{df.columns.tolist()}")

    # 处理地址格式（去除换行符和分号）
    if 'address' in df.columns:
        df['address'] = df['address'].apply(lambda x: re.sub(r'[\n;]', ', ', str(x)).strip() if pd.notna(x) else x)

    # 添加longitude和latitude列（在name列后面）
    # 找到name列的位置
    name_col_idx = df.columns.get_loc('name')
    
    # 在name列后插入longitude和latitude列
    df.insert(name_col_idx + 1, 'longitude', None)
    df.insert(name_col_idx + 2, 'latitude', None)

    # 高德API配置 - 请替换为你的API key
    API_KEY = "你的高德地图API密钥"  # 需要替换为实际的API key
    
    if API_KEY == "你的高德地图API密钥":
        print("=" * 50)
        print("请先设置你的高德地图API密钥！")
        print("=" * 50)
        print("使用说明：")
        print("1. 访问 https://console.amap.com/ 获取你的API密钥")
        print("2. 将代码中的 API_KEY = \"你的高德地图API密钥\" 替换为你的实际API key")
        print("3. 重新运行程序")
        print("=" * 50)
        # 为了演示，这里使用一个示例key，实际使用时请替换
        API_KEY = "dd0d37d775bb0c24a774caf122511afa"
        print(f"当前使用演示API密钥：{API_KEY}")
        print("=" * 50)

    # 批量处理
    success_count = 0
    fail_count = 0
    
    for idx, row in df.iterrows():
        address = row.get('address', '')
        name = row.get('name', '')
        
        if pd.isna(address) or address == '':
            print(f"第{idx + 1}行：地址为空，跳过")
            fail_count += 1
            continue
            
        print(f"正在处理第{idx + 1}行：{name} - {address}")
        
        try:
            lng, lat = get_lng_lat(address, API_KEY)
            
            if lng is not None and lat is not None:
                df.at[idx, 'longitude'] = lng
                df.at[idx, 'latitude'] = lat
                success_count += 1
                print(f"  成功获取坐标：经度{lng}, 纬度{lat}")
            else:
                fail_count += 1
                print(f"  获取坐标失败")
                
        except Exception as e:
            fail_count += 1
            print(f"  处理出错：{str(e)}")
        
        sleep(0.5)  # 防止请求过快

    # 保存结果
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\n处理完成！")
    print(f"成功获取坐标：{success_count}个")
    print(f"失败：{fail_count}个")
    print(f"结果已保存到：{output_file.resolve()}")

except Exception as e:
    print("程序运行中断！")
    print(f"错误详情：{str(e)}")
    traceback.print_exc()