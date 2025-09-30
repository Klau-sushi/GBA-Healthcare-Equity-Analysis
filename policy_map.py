# 导入我们需要的库
import pandas as pd
import folium
import requests
import os
import geopandas as gpd  # ★ 新增：导入强大的地理数据处理库
import branca.colormap as cm  # ★ 新增：导入色带库，用于手动创建图例

# --- 第0步：定义所有需要用到的文件名和URL ---
geojson_filename = 'shenzhen_districts.geojson'
geojson_url = 'https://geo.datav.aliyun.com/areas_v3/bound/440300_full.json'
density_filename = 'district_density.xlsx' 
main_data_filename = 'shenzhen_poi_data.xlsx'
anchors_filename = 'anchors.xlsx'

# --- 第1步：智能下载GeoJSON文件 ---
if not os.path.exists(geojson_filename):
    print(f"本地未找到地图边界文件 '{geojson_filename}'，现在开始自动下载...")
    try:
        response = requests.get(geojson_url)
        response.raise_for_status()
        with open(geojson_filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("地图边界文件下载并保存成功！")
    except requests.exceptions.RequestException as e:
        print(f"下载地图边界文件失败: {e}")
        print("请检查您的网络连接，然后重试。")
        exit()
else:
    print(f"本地已存在地图边界文件 '{geojson_filename}'，无需下载。")

# --- 第2步：读取您的所有本地数据文件 ---
try:
    df_main = pd.read_excel(main_data_filename)
    df_anchors = pd.read_excel(anchors_filename)
    df_density = pd.read_excel(density_filename) # ★ 新增：读取我们统计的密度数据
except FileNotFoundError as e:
    print(f"文件未找到: {e}。请确保所有Excel和geojson文件都在同一个文件夹下，且文件名正确。")
    exit()

# --- 第3步：创建一张基础地图 ---
m = folium.Map(location=[22.54, 114.05], zoom_start=11, tiles='CartoDB positron')

# --- 第4步：创建不同的图层组 (用于放置数据点) ---
layer_base = folium.FeatureGroup(name='普通三甲 (Baseline Tier-A)')
layer_policy_tier_a = folium.FeatureGroup(name='药械通指定-三甲 (Policy Designated - Tier A)')
layer_policy_non_tier_a = folium.FeatureGroup(name='药械通指定-非三甲 (Policy Designated - Non Tier A)')
layer_anchors = folium.FeatureGroup(name='跨境口岸 (Border Crossings)')
layer_districts_lines = folium.FeatureGroup(name='行政区划边界线', show=True) # ★ 为独立的边界线创建一个新图层

# --- 第5步：创建核心的“分级统计地图”和独立的“边界线”图层 ---
# 1. 读取并合并数据 (和之前一样)
shenzhen_geo = gpd.read_file(geojson_filename)
merged_geo_data = shenzhen_geo.merge(df_density, left_on='name', right_on='district', how='left')
merged_geo_data['count'] = merged_geo_data['count'].fillna(0)

# 2. ★ 绘制“热力图”图层 (只填充颜色，不画边框)
folium.Choropleth(
    geo_data=merged_geo_data,
    name='“药械通”医院区域密度', # 在图层控制器中显示的名称
    data=merged_geo_data,
    columns=['district', 'count'],
    key_on='feature.properties.district',
    fill_color='BuGn', # 您选择的蓝绿色带
    fill_opacity=0.7,
    line_opacity=0, # ★ 关键修改：将线条透明度设为0，即不画边框
    legend_name='“药械通”医院区域密度',
    overlay=True,
    show=True
).add_to(m)

# 3. ★ 绘制独立的“边界线”图层 (只画边框，不填充颜色)
style_function_lines_only = lambda x: {'color': 'grey', 'weight': 1, 'dashArray': '5, 5', 'fillOpacity': 0.0}
#    ★★★★★ 终极修正：在这里也强制使用UTF-8编码读取文件 ★★★★★
folium.GeoJson(
    open(geojson_filename, 'r', encoding='utf-8').read(), # ★ 关键修正就在这里！
    name='Shenzhen District Lines',
    style_function=style_function_lines_only,
    interactive=False # 确保它不可交互
).add_to(layer_districts_lines) # ★ 将这个图层添加到我们新建的FeatureGroup中

# --- 第6步：将Excel中的数据点添加到对应的图层上 ---
# (这部分代码和之前完全一样)
for idx, row in df_main.iterrows():
    try:
        lat = float(row['latitude'])
        lon = float(row['longitude'])
        hospital_type = str(row['type']).strip()
    except (ValueError, TypeError): continue
    if hospital_type == 'Tier_A_Only':
        popup = folium.Popup(f"{row['name']}<br>(普通三甲)", max_width=250)
        folium.CircleMarker(location=[lat, lon], radius=4, color='lightblack', fill=True, fill_color='lightblack', fill_opacity=0.5, popup=popup).add_to(layer_base)
    elif hospital_type == 'Policy_Designated':
        popup = folium.Popup(f"<strong>{row['name']}</strong><br>(药械通指定-三甲)", max_width=250)
        folium.CircleMarker(location=[lat, lon], radius=6, color='red', fill=True, fill_color='red', fill_opacity=0.8, popup=popup).add_to(layer_policy_tier_a)
    elif hospital_type == 'Non_Tier_A_Policy':
        popup = folium.Popup(f"<strong>{row['name']}</strong><br>(药械通指定-非三甲)", max_width=250)
        folium.CircleMarker(location=[lat, lon], radius=6, color='#336e99', fill=True, fill_color='#336e99', fill_opacity=0.7, popup=popup).add_to(layer_policy_non_tier_a)

for idx, row in df_anchors.iterrows():
    popup = folium.Popup(f"<strong>{row['name']}</strong>", max_width=250)
    folium.Marker(location=[row['latitude'], row['longitude']], popup=popup, icon=folium.Icon(color='purple', icon='star')).add_to(layer_anchors)

# --- 第7步：将所有图层组一次性添加到地图上 ---
layer_base.add_to(m)
layer_policy_tier_a.add_to(m)
layer_policy_non_tier_a.add_to(m)
layer_anchors.add_to(m)
layer_districts_lines.add_to(m) # ★ 将我们独立的边界线图层添加到地图上

# --- 第8步：添加图层控制器和“终极版”自定义图例 ---
folium.LayerControl().add_to(m)

# ==============================================================================
# --- ★★★★★ 终极布局优化：分离图例，精确定位 ★★★★★ ---
# ==============================================================================

# 1. ★ 构建“药械通医院区域密度”图例（垂直、离散、无背景框）
#    我们将它放在地图的左下角，位于标记点图例的“上方”
colormap = cm.linear.BuGn_09.scale(vmin=0, vmax=merged_geo_data['count'].max())
density_title = '<b>“药械通”医院区域密度</b>'
#    关键修改：调整 bottom 和 left 的值，并设置透明背景
legend_html_density = f'<div style="position: fixed; bottom: 185px; left: 50px; z-index:9998; font-size:14px; background-color: rgba(255, 255, 255, 0.0);">'
legend_html_density += f'<h4 style="margin: 0 0 5px 0; text-align: left; color: #333; text-shadow: -1px -1px 0 #FFF, 1px -1px 0 #FFF, -1px 1px 0 #FFF, 1px 1px 0 #FFF;">{density_title}</h4>'
legend_html_density += '<ul style="list-style: none; padding: 0; margin: 0;">'
bins = [0, 2, 4, 6, 8] # 0-1, 2-3, 4-5, 6+
for i in range(len(bins)-1):
    lower_bound = bins[i]
    upper_bound = bins[i+1] - 1
    color = colormap.rgb_hex_str((lower_bound + upper_bound) / 2)
    label = f"{lower_bound} - {upper_bound}" if i < len(bins)-2 else f"{lower_bound}+"
    # ★ 给文字加上白色描边，让它在任何地图背景上都清晰可见
    legend_html_density += f'<li style="margin: 5px 0; color: #333; text-shadow: -1px -1px 0 #FFF, 1px -1px 0 #FFF, -1px 1px 0 #FFF, 1px 1px 0 #FFF;"><span style="background-color: {color}; width: 20px; height: 20px; display: inline-block; margin-right: 5px; vertical-align: middle; border: 1px solid #ccc;"></span>{label}</li>'
legend_html_density += '</ul></div>'
m.get_root().html.add_child(folium.Element(legend_html_density))


# 2. ★ 构建“医疗资源图例”（标记点图例，保留白色背景框）
#    我们依然将它放在地图的左下角（bottom: 50px）
legend_html_markers = '''
     <div style="position: fixed; bottom: 50px; left: 50px; width: 280px; height: 120px;
     background-color: white; border:2px solid grey; z-index:9999; font-size:14px;">
     &nbsp; <b>医疗资源图例</b><br>
     &nbsp; <i class="fa fa-circle" style="color:lightblack"></i>&nbsp; 普通三甲医院<br>
     &nbsp; <i class="fa fa-circle" style="color:red"></i>&nbsp; “药械通”指定医院 (三甲)<br>
     &nbsp; <i class="fa fa-circle" style="color:#336e99"></i>&nbsp; “药械通”指定医院 (非三甲)<br>
     &nbsp; <i class="fa fa-star" style="color:purple"></i>&nbsp; 主要跨境口岸<br>
     </div>
     '''
m.get_root().html.add_child(folium.Element(legend_html_markers))


# 3. ★ 添加CSS代码，强制隐藏folium自动生成的那个我们不想要的连续图例
hide_legend_css = '''
<style>
.leaflet-control-container .leaflet-top.leaflet-right > .legend { display: none !important; }
</style>
'''
m.get_root().header.add_child(folium.Element(hide_legend_css))

# ==============================================================================

# --- 第9步：保存最终的地图文件 ---
output_map = '港澳药械通政策空间评估地图_密度热力版.html'
m.save(output_map)
print(f"终极版“密度热力”地图已生成！请用浏览器打开 {output_map}")