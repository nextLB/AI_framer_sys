import os
import shutil
import random
import argparse
from pathlib import Path
from tqdm import tqdm
from PIL import Image


def convert_bbox_to_yolo(size, box):
    """将边界框转换为 YOLO 格式 (归一化的中心点 + 宽高)"""
    dw = 1.0 / size[0]
    dh = 1.0 / size[1]
    x_center = (box[0] + box[1]) / 2.0
    y_center = (box[2] + box[3]) / 2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    return (x_center * dw, y_center * dh, w * dw, h * dh)


def get_all_images_and_labels(dataset_path):
    """获取所有图片和对应的类别"""
    class_names = sorted([d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))])
    class_to_idx = {name: idx for idx, name in enumerate(class_names)}
    
    images_info = []
    for class_name in class_names:
        class_dir = os.path.join(dataset_path, class_name)
        class_idx = class_to_idx[class_name]
        
        for img_file in os.listdir(class_dir):
            if img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                img_path = os.path.join(class_dir, img_file)
                images_info.append({
                    'image_path': img_path,
                    'class_idx': class_idx,
                    'class_name': class_name
                })
    
    return class_names, images_info


def process_images_to_yolo_format(images_info, output_dir, split='train'):
    """处理图片，生成 YOLO 格式的标注（整图作为单个目标）"""
    output_images_dir = os.path.join(output_dir, 'images', split)
    output_labels_dir = os.path.join(output_dir, 'labels', split)
    
    os.makedirs(output_images_dir, exist_ok=True)
    os.makedirs(output_labels_dir, exist_ok=True)
    
    processed_count = 0
    error_count = 0
    
    for info in tqdm(images_info, desc=f"Processing {split}"):
        try:
            img_path = info['image_path']
            
            with Image.open(img_path) as img:
                img_width, img_height = img.size
            
            img_name = Path(img_path).stem
            new_img_name = f"{info['class_name']}_{img_name}.jpg"
            
            new_img_path = os.path.join(output_images_dir, new_img_name)
            new_label_path = os.path.join(output_labels_dir, new_img_name.replace('.jpg', '.txt').replace('.png', '.txt'))
            
            shutil.copy2(img_path, new_img_path)
            
            with open(new_label_path, 'w') as f:
                cls_idx = info['class_idx']
                f.write(f"{cls_idx} 0.5 0.5 1.0 1.0\n")
            
            processed_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"Error processing {img_path}: {e}")
    
    return processed_count, error_count


def create_yaml_config(class_names, output_dir):
    """创建 YOLO 数据集配置文件"""
    yaml_content = f"""# Agricultural Plant Disease Dataset (YOLO Format)
# Classes: {len(class_names)}

path: {os.path.abspath(output_dir)}
train: images/train
val: images/val
test: images/test

nc: {len(class_names)}
names:
"""
    
    for idx, class_name in enumerate(class_names):
        yaml_content += f"  {idx}: {class_name}\n"
    
    yaml_path = os.path.join(output_dir, 'dataset.yaml')
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    return yaml_path


def main():
    parser = argparse.ArgumentParser(description='Convert PlantVillage dataset to YOLO format')
    parser.add_argument('--dataset', type=str, 
                        default='/home/next_lb/桌面/next/基于AI的农业植保机器人监控软件系统/datasets/',
                        help='Path to original dataset directory')
    parser.add_argument('--output', type=str, 
                        default='/home/next_lb/桌面/next/基于AI的农业植保机器人监控软件系统/datasets/yolo_dataset',
                        help='Output directory for YOLO format dataset')
    parser.add_argument('--train-ratio', type=float, default=0.7,
                        help='Training set ratio (default: 0.7)')
    parser.add_argument('--val-ratio', type=float, default=0.2,
                        help='Validation set ratio (default: 0.2)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    random.seed(args.seed)
    
    print("=" * 60)
    print("PlantVillage Dataset to YOLO Format Converter")
    print("=" * 60)
    
    if not os.path.exists(args.dataset):
        print(f"Error: Dataset directory not found: {args.dataset}")
        return
    
    print(f"\n[1/5] Scanning dataset from: {args.dataset}")
    class_names, images_info = get_all_images_and_labels(args.dataset)
    print(f"Found {len(class_names)} classes with {len(images_info)} images:")
    for idx, name in enumerate(class_names):
        count = sum(1 for i in images_info if i['class_name'] == name)
        print(f"  {idx}: {name} ({count} images)")
    
    print(f"\n[2/5] Splitting dataset (train:{args.train_ratio}, val:{args.val_ratio}, test:{1-args.train_ratio-args.val_ratio})")
    random.shuffle(images_info)
    
    total = len(images_info)
    train_end = int(total * args.train_ratio)
    val_end = train_end + int(total * args.val_ratio)
    
    train_images = images_info[:train_end]
    val_images = images_info[train_end:val_end]
    test_images = images_info[val_end:]
    
    print(f"  Train: {len(train_images)} images")
    print(f"  Val: {len(val_images)} images")
    print(f"  Test: {len(test_images)} images")
    
    print(f"\n[3/5] Creating output directories...")
    os.makedirs(args.output, exist_ok=True)
    
    print(f"\n[4/5] Converting images to YOLO format...")
    train_count, train_errors = process_images_to_yolo_format(train_images, args.output, 'train')
    val_count, val_errors = process_images_to_yolo_format(val_images, args.output, 'val')
    test_count, test_errors = process_images_to_yolo_format(test_images, args.output, 'test')
    
    print(f"\n[5/5] Creating dataset.yaml configuration...")
    yaml_path = create_yaml_config(class_names, args.output)
    
    print("\n" + "=" * 60)
    print("Conversion Complete!")
    print("=" * 60)
    print(f"Total processed: {train_count + val_count + test_count}")
    print(f"Total errors: {train_errors + val_errors + test_errors}")
    print(f"\nOutput directory: {os.path.abspath(args.output)}")
    print(f"Config file: {yaml_path}")
    print("\nNext step: python 2_train_yolov8.py")


if __name__ == '__main__':
    main()
