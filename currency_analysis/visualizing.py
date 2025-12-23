import cv2
import numpy as np


class Cv2Visualizer:

    _colors = {
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
    }

    @classmethod
    def show(cls,
             img_array: np.ndarray,
             name: str = "Image"):
        cv2.imshow(name, img_array)
        cv2.waitKey(0)

    @classmethod
    def draw_rectangle(cls,
                       img_array: np.ndarray,
                       x, y, w, h,
                       color: str,
                       inplace: bool,
                       thickness: int = 1) -> np.ndarray | None:
        img_array = img_array if inplace else img_array.copy()

        color_nums = cls._colors[color]
        cv2.rectangle(img_array,
                      (x, y),
                      (x + w, y + h),
                      color=color_nums,
                      thickness=thickness)

        if not inplace:
            return img_array

        return None

    def draw_circle(self,
                    img_array: np.ndarray,
                    cx, cy, r):
        cv2.circle(img_array,
                   (cx, cy),
                   r,
                   (0, 255, 0),
                   1)
