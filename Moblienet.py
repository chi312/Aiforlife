# Import necessary libraries
from silence_tensorflow import silence_tensorflow
silence_tensorflow()

import os
import cv2
import warnings
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from keras.utils import plot_model
from tensorflow.keras import optimizers, regularizers, models, layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, LearningRateScheduler
from sklearn.metrics import classification_report, confusion_matrix, mean_absolute_error, mean_squared_error

sns.set_style('darkgrid')
warnings.filterwarnings('ignore')

# Path setup
base_dir = 'dataai'
train_dir = os.path.join(base_dir, 'train')
validation_dir = os.path.join(base_dir, 'validation')
test_dir = os.path.join(base_dir, 'test')


# Function to count classes
def num_of_classes(folder_dir, folder_name):
    classes = [class_name for class_name in os.listdir(folder_dir)]
    print(f'Number of classes in {folder_name} folder: {len(classes)}')


# Count classes
num_of_classes(train_dir, 'train')
num_of_classes(validation_dir, 'validation')
num_of_classes(test_dir, 'test')


# Prepare DataFrame
def create_df(folder_path):
    all_images = []
    classes = [class_name for class_name in os.listdir(folder_path)]
    for class_name in classes:
        class_path = os.path.join(folder_path, class_name)
        all_images.extend([(os.path.join(class_path, file_name), class_name) for file_name in os.listdir(class_path)])
    df = pd.DataFrame(all_images, columns=['file_path', 'label'])
    return df


train_df = create_df(train_dir)
validation_df = create_df(validation_dir)
test_df = create_df(test_dir)

# Data Generators
train_datagen = ImageDataGenerator(
    rescale=1. / 255,
    rotation_range=30,
    width_shift_range=0.3,
    height_shift_range=0.3,
    zoom_range=0.2,
    horizontal_flip=True,
    vertical_flip=True,
    shear_range=0.2,
    fill_mode='nearest',
)

train_generator = train_datagen.flow_from_dataframe(
    dataframe=train_df,
    x_col='file_path',
    y_col='label',
    target_size=(224, 224),
    color_mode='rgb',
    class_mode='categorical',
    batch_size=32,
    shuffle=True,
    seed=42,
)

validation_datagen = ImageDataGenerator(rescale=1. / 255)
validation_generator = validation_datagen.flow_from_dataframe(
    dataframe=validation_df,
    x_col='file_path',
    y_col='label',
    target_size=(224, 224),
    class_mode='categorical',
    batch_size=32,
    seed=42,
    shuffle=False,
)

test_datagen = ImageDataGenerator(rescale=1. / 255)
test_generator = test_datagen.flow_from_dataframe(
    dataframe=test_df,
    x_col='file_path',
    y_col='label',
    target_size=(224, 224),
    class_mode='categorical',
    batch_size=32,
    seed=42,
    shuffle=False,
)

# Model setup
pre_trained_model = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights='imagenet',
    pooling='avg'
)

# Freeze layers
pre_trained_model.trainable = True
set_trainable = False

for layer in pre_trained_model.layers:
    if layer.name == 'block_16_expand':
        set_trainable = True
    if set_trainable:
        layer.trainable = True
    else:
        layer.trainable = False

# Add custom layers with regularization and dropout
model = models.Sequential([
    pre_trained_model,
    layers.Flatten(),
    layers.Dense(256, activation='relu', kernel_regularizer=regularizers.l2(0.001)),
    layers.Dropout(0.4),
    layers.BatchNormalization(),
    layers.Dense(128, activation='relu', kernel_regularizer=regularizers.l2(0.001)),
    layers.Dropout(0.4),
    layers.BatchNormalization(),
    layers.Dense(5, activation='softmax')
])

# Compile model with a lower learning rate
model.compile(
    optimizer=optimizers.Adam(learning_rate=0.001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)


# Learning Rate Scheduler
def lr_schedule(epoch):
    initial_lr = 0.001
    if epoch > 20:
        return initial_lr * 0.5
    elif epoch > 50:
        return initial_lr * 0.1
    return initial_lr


lr_scheduler = LearningRateScheduler(lr_schedule)

# Callbacks
checkpoint_cb = ModelCheckpoint('BestModel.keras', save_best_only=True)
earlystop_cb = EarlyStopping(patience=20, restore_best_weights=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6)

# Adjust validation_steps to match training steps
validation_steps = len(validation_generator)

# Train model
history = model.fit(
    train_generator,
    steps_per_epoch=len(train_generator),
    epochs=300,
    validation_data=validation_generator,
    validation_steps=validation_steps,  # Adjusted
    callbacks=[checkpoint_cb, earlystop_cb, reduce_lr, lr_scheduler]
)


# Combined Accuracy and Loss Plot
def plot_training_history_combined(history):
    # Find the minimum length between training and validation history
    min_length = min(len(history.history['accuracy']), len(history.history['val_accuracy']))

    # Adjust epochs to the smaller length
    epochs = range(1, min_length + 1)

    plt.figure(figsize=(12, 6))

    # Plot accuracy on primary y-axis
    plt.plot(epochs, history.history['accuracy'][:min_length], '-o', color='blue', label='Training Accuracy')
    plt.plot(epochs, history.history['val_accuracy'][:min_length], '-o', color='green', label='Validation Accuracy')

    # Annotate accuracy points
    for i, val in enumerate(history.history['val_accuracy'][:min_length]):
        plt.text(epochs[i], val, f'{val:.2%}', fontsize=8, ha='center', va='bottom', color='green')

    # Set up the secondary y-axis for loss
    ax2 = plt.gca().twinx()
    ax2.plot(epochs, history.history['loss'][:min_length], '-o', color='red', label='Training Loss')
    ax2.plot(epochs, history.history['val_loss'][:min_length], '-o', color='orange', label='Validation Loss')

    # Annotate loss points
    for i, val in enumerate(history.history['val_loss'][:min_length]):
        ax2.text(epochs[i], val, f'{val:.2f}', fontsize=8, ha='center', va='bottom', color='orange')

    # Titles and labels
    plt.title('Training and Validation Accuracy and Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    ax2.set_ylabel('Loss')

    # Combine legends from both axes
    lines, labels = plt.gca().get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    plt.legend(lines + lines2, labels + labels2, loc='upper center')

    plt.tight_layout()
    plt.show()


def plot_confusion_matrix(cm, class_names, title='Confusion Matrix'):
    plt.figure(figsize=(8, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.title(title)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.tight_layout()
    plt.show()


# Evaluate the best model on the validation set
best_model = models.load_model('BestModel.keras')
val_loss, val_acc = best_model.evaluate(validation_generator, verbose=0)
print(f"\nBest Validation Loss: {val_loss:.4f}")
print(f"Best Validation Accuracy: {val_acc:.4%}")

# Make predictions on the validation set
predictions = best_model.predict(validation_generator)
predicted_classes = np.argmax(predictions, axis=1)
true_classes = validation_generator.classes
class_labels = list(validation_generator.class_indices.keys())

# Classification Report on Validation Set
report = classification_report(true_classes, predicted_classes, target_names=class_labels, output_dict=True)
print("\nValidation Classification Report:")
print(classification_report(true_classes, predicted_classes, target_names=class_labels))

# Confusion Matrix on Validation Set
cm_val = confusion_matrix(true_classes, predicted_classes)
plot_confusion_matrix(cm_val, class_labels, title='Validation Confusion Matrix')

# Calculate additional metrics on Validation Set
mae_val = mean_absolute_error(true_classes, predicted_classes)
rmse_val = mean_squared_error(true_classes, predicted_classes, squared=False)
print(f"\nValidation MAE: {mae_val:.4f}")
print(f"Validation RMSE: {rmse_val:.4f}")

# Evaluate the best model on the test set
test_loss, test_acc = best_model.evaluate(test_generator, verbose=0)
print(f"\nTest Loss: {test_loss:.4f}")
print(f"Test Accuracy: {test_acc:.4%}")

# Make predictions on the test set
predictions_test = best_model.predict(test_generator)
predicted_classes_test = np.argmax(predictions_test, axis=1)
true_classes_test = test_generator.classes

# Classification Report on Test Set
report_test = classification_report(true_classes_test, predicted_classes_test, target_names=class_labels, output_dict=True)
print("\nTest Classification Report:")
print(classification_report(true_classes_test, predicted_classes_test, target_names=class_labels))

# Confusion Matrix on Test Set
cm_test = confusion_matrix(true_classes_test, predicted_classes_test)
plot_confusion_matrix(cm_test, class_labels, title='Test Confusion Matrix')

# Calculate additional metrics on Test Set
mae_test = mean_absolute_error(true_classes_test, predicted_classes_test)
rmse_test = mean_squared_error(true_classes_test, predicted_classes_test, squared=False)
print(f"\nTest MAE: {mae_test:.4f}")
print(f"Test RMSE: {rmse_test:.4f}")

# Plot training history
plot_training_history_combined(history)

# Save the final model
model.save('FinalModel_4.keras')