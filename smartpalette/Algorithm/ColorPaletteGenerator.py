#author: Devan Corcoran

import random
import math
from PIL import Image


class PaletteGenerator:

    @staticmethod
    def create_palette(image, num_of_colors):

        pixel_list = list(Image.open(image, 'r').getdata())

        x_list = []
        y_list = []
        z_list = []
        x_means = []
        y_means = []
        z_means = []

        for each in pixel_list:
            x_list.append(each[0])
            y_list.append(each[1])
            z_list.append(each[2])

        for i in range(num_of_colors):
            x_means.append(random.randint(0, 255))
            y_means.append(random.randint(0, 255))
            z_means.append(random.randint(0, 255))

        change = 1
        while change > 0.00001:
            
            catlist = PaletteGenerator.categorize(x_list, y_list, z_list, x_means, y_means, z_means)

            x_means, y_means, z_means, change = PaletteGenerator.refine_mean(
                num_of_colors, catlist, x_list, y_list, z_list, x_means, y_means, z_means
            )

            x_means = PaletteGenerator.eliminateNoneVals(x_means)
            y_means = PaletteGenerator.eliminateNoneVals(y_means)
            z_means = PaletteGenerator.eliminateNoneVals(z_means)

            new_len = len(x_means)

            num_of_colors = new_len


        color_list = []
        for i in range(len(x_means)):
            r, g, b = x_means[i], y_means[i], z_means[i]
            color_list.append([r,g,b])

        return color_list

    @staticmethod
    def categorize(x, y, z, xmeans, ymeans, zmeans):


        catlist = []

        category = 0

        for i in range(len(x)):
            xpoint = x[i]
            ypoint = y[i]
            zpoint = z[i]

            best_distance = 100000000000000
            for j in range(len(xmeans)):
                xm = xmeans[j]
                ym = ymeans[j]
                zm = zmeans[j]
                distance = math.sqrt(((xm-xpoint)**2)+((ym-ypoint)**2)+((zm-zpoint)**2))

                if distance < best_distance:
                    best_distance = distance
                    category = j
            catlist.append(category)

        return catlist

    @staticmethod


    def eliminateNoneVals(element_list):


        for item in element_list:

            if item == None:

                element_list.remove(item)

        return element_list


    def refine_mean(palette_num, catlist, xlist, ylist, zlist, xmeans, ymeans, zmeans):


        newxmeans = []
        newymeans = []
        newzmeans = []

        change = 0
        for j in range(palette_num):
            xsum = ysum = zsum = catcount = count = 0

            for cat in catlist:
                if cat == j:
                    x = xlist[count]
                    y = ylist[count]
                    z = zlist[count]

                    xsum += x
                    ysum += y
                    zsum += z
                    catcount += 1
                count += 1

            if count != 0 and catcount !=0:
                meanx = xsum//catcount
                meany = ysum//catcount
                meanz = zsum//catcount

                change += abs(meanx-xmeans[j])

                newxmeans.append(meanx)
                newymeans.append(meany)
                newzmeans.append(meanz)
            elif catcount != 0:
                newxmeans.append(xmeans[j])
                newymeans.append(ymeans[j])
                newzmeans.append(zmeans[j])
                
            else:
                newxmeans.append(None)
                newymeans.append(None)
                newzmeans.append(None)

        return newxmeans, newymeans, newzmeans, change


def main():
    a = PaletteGenerator()
    user_image = input("Enter the file name: ")

    palette_num = int(input("How many colors would you like on the palette? "))

    color_list = a.create_palette(user_image, palette_num)
    print(color_list)

if __name__ == "__main__":
    main()
