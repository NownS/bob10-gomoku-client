import numpy as np

gomoku_default_weight_map = np.array([
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,1,1,0,0,0,0,0,0],
        [0,0,0,0,1,1,1,2,1,1,1,0,0,0,0],
        [0,0,0,1,1,1,2,3,2,1,1,1,0,0,0],
        [0,0,1,1,1,2,3,4,3,2,1,1,1,0,0],
        [0,0,1,1,2,3,4,5,4,3,2,1,1,0,0],
        [0,1,1,2,3,4,5,6,5,4,3,2,1,1,0],
        [0,1,2,3,4,5,6,7,6,5,4,3,2,1,0],
        [0,1,1,2,3,4,5,6,5,4,3,2,1,1,0],
        [0,0,1,1,2,3,4,5,4,3,2,1,1,0,0],
        [0,0,1,1,1,2,3,4,3,2,1,1,1,0,0],
        [0,0,0,1,1,1,2,3,2,1,1,1,0,0,0],
        [0,0,0,0,1,1,1,2,1,1,1,0,0,0,0],
        [0,0,0,0,0,0,1,1,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ])
gomoku_default_weight_map = gomoku_default_weight_map / 10

gomoku_weight_map = None

moves = ((1,0), (0,1), (1,1), (1,-1))

WHITE = 1
BLACK = 0
BLANK = -1



class Generator:
    def __init__(self, color, gomoku_map):
        self.map = gomoku_map
        self.color = color


    def gen_xy(self, my_color):                           # 위치별 가중치 가장 높은 위치 리턴
        
        global gomoku_weight_map
        gomoku_weight_map = np.array([[0 for _ in range(15)] for _ in range(15)]) # init
        my_max_weight = 0
        your_max_weight = 0
        max_weight = 0

        for x in range(15):
            for y in range(15):
                my_weight = self.calculate_weight(x, y, my_color) + gomoku_default_weight_map[x][y]
                your_weight = self.calculate_weight(x, y, int(not my_color)) + gomoku_default_weight_map[x][y]
                
                if my_weight >= 10000:
                    return x,y
                elif your_weight >= 10000 and my_weight != -1:
                    your_weight = 10000

                if max_weight < my_weight + your_weight and my_weight != -1:
                    max_weight = my_weight + your_weight
                    max_xy = [x,y]

                if my_max_weight < my_weight and my_weight != -1:
                    my_max_weight = my_weight
                    my_xy = [x,y]

                if your_max_weight < your_weight:
                    your_max_weight = your_weight

        if my_max_weight >= your_max_weight:
            return my_xy
        else:
            return max_xy
                


    def calculate_weight(self, x, y, color):        # 좌표별 가중치 계산
        board = self.map
        if board[x][y] != -1 :
            return 0

        two_1 = ['001010','010100','010010']
        two_2 = ['01100', '00110']
        three_6 = ['010110', '011010']
        three_8 = '01110'
        four_8 = ['10111','11011','11101']
        four_10 = ['11110','01111']
        four_50 =  '011110'

        weight = 0
        three_count = 0
        four_count = 0
        open_three_count = 0
        open_four_count = 0

        # 양방향으로 체크할것이기 때문에 for문은 4방향.
        for i in range(4):
            check_pattern = '1'
            x_check = x
            y_check = y
            for j in range(4):
                x_check += moves[i][0]
                y_check += moves[i][1]
                if x_check < 0 or x_check >= 15 or y_check < 0 or y_check >= 15:
                    break

                check_xy = board[x_check][y_check]
                if x_check < 0 or x_check >= 15 or y_check < 0 or y_check >= 15:
                        break
                if check_xy == color:
                    check_pattern = '1' + check_pattern
                elif check_xy == BLANK:
                    check_pattern = '0' + check_pattern
                else:
                    break
            x_check = x
            y_check = y
            for j in range(4):
                x_check -= moves[i][0]
                y_check -= moves[i][1]
                if x_check < 0 or x_check >= 15 or y_check < 0 or y_check >= 15:
                    break

                check_xy = board[x_check][y_check]
                if x_check < 0 or x_check >= 15 or y_check < 0 or y_check >= 15:
                        break
                if check_xy == color:
                    check_pattern = check_pattern + '1'
                elif check_xy == BLANK:
                    check_pattern = check_pattern + '0'
                else:
                    break

            for three in three_6:
                if three in check_pattern and (not ('11101' in check_pattern)) and (not ('10111' in check_pattern)):
                    weight += 6
                    three_count += 1

            if three_8 in check_pattern and (not ('11101' in check_pattern)) and (not ('10111' in check_pattern)):
                weight += 8
                three_count += 1
            
            if three_8 in check_pattern:
                open_three_count += 1
                if open_three_count == 2 and color == BLACK:
                    return 0

            if '11111' in check_pattern:
                if color == WHITE:
                    return 10000
                else:
                    if '111111' in check_pattern:
                        continue
                    else:
                        return 10000

            if four_50 in check_pattern:
                weight += 50
                open_four_count += 1
                if open_four_count == 2 and color == BLACK:
                    return 0

            for two in two_1:
                if two in check_pattern:
                    weight += 1

            for two in two_2:
                if two in check_pattern:
                    weight += 2

            for four in four_8:
                if four in check_pattern:
                    weight += 8
                    four_count += 1
                    if four_count + three_count > 1:
                        weight += 150

            for four in four_10:
                if four in check_pattern:
                    weight += 10
                    four_count += 1
                    if four_count + three_count > 1:
                        weight += 150

        return weight

    # def find_best_point(self, n):                              # 가장 가중치 높은 좌표(x, y, val) n개 뽑아내기
    #     all = []
    #     for i in range(15):
    #         for j in range(15):
    #             all.append((i, j, gomoku_weight_map[i][j]))
                
    #     all.sort(key=lambda x: -x[2])

    #     return all[:n] if n <= len(all) else all

    # def minmax():

    #     current_map = deepcopy(gomoku_map)

    #     set_weight(my_color)
    #     pos_value_list = find_best_point(10)
    #     for x, y, val in pos_value_list:
    #         pass
    

    # def gen_xy(self):                           # generate x,y algorithm
    #     while True:
    #         self.set_weight(self.color)
    #         x, y, weight = self.find_best_point(1)[0]
    #         if self.gomoku_map[x][y] == BLANK:
    #             return x, y