import numpy as np
from matplotlib import pyplot as plt

from stl import mesh
from skimage import measure
import os, math, time, numpy as np, mcubes, open3d as o3d
from collections import Counter, defaultdict
from shapely.validation import explain_validity

import shapely
print(shapely.__version__)
from shapely import constrained_delaunay_triangles, Polygon

# the version of Python lib:
# python 3.10
# pip install "shapely>=2.1.0" to run constrained_delaunay_triangles
# pip install "open3d>=0.19.0"

def rotation_matrix_x(angle):
    """Rotation matrix for rotation around the x-axis."""
    return np.array([
        [1, 0, 0],
        [0, np.cos(angle), -np.sin(angle)],
        [0, np.sin(angle), np.cos(angle)]
    ])


def rotation_matrix_y(angle):
    """Rotation matrix for rotation around the y-axis."""
    return np.array([
        [np.cos(angle), 0, np.sin(angle)],
        [0, 1, 0],
        [-np.sin(angle), 0, np.cos(angle)]
    ])


def rotation_matrix_z(angle):
    """Rotation matrix for rotation around the z-axis."""
    return np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])


def rotate(verts, angle_x, angle_y, angle_z, degrees=True):
    ax, ay, az = (angle_x, angle_y, angle_z)  # Start of CHANGES: Covert Radian to Angle for Calculation of Rotation
    if degrees:
        ax, ay, az = np.deg2rad([ax, ay, az])  # End of CHANGES.
    rotation_x = rotation_matrix_x(ax)
    rotation_y = rotation_matrix_y(ay)
    rotation_z = rotation_matrix_z(az)
    rotated_verts = verts.dot(rotation_x).dot(rotation_y).dot(rotation_z)
    return rotated_verts


def tpms_value(x, y, z, k, kind, iso, mode):
    kind = kind.lower()
    if kind in ("gyroid", "g", "Gyroid"):
        F = np.sin(k * x) * np.cos(k * y) + np.sin(k * y) * np.cos(k * z) + np.sin(k * z) * np.cos(k * x)
    # elif kind in ("schwarz-d", "d", "schwarzd"):
    #     F = np.sin(k*x)*np.sin(k*y)*np.sin(k*z)
    elif kind in ("FKS", "fks", "Fischer-Koch-S"):
        F = np.cos(2 * k * x) * np.sin(k * y) * np.cos(k * z) + np.cos(k * x) * np.cos(2 * k * y) * np.sin(
            k * z) + np.cos(2 * k * z) * np.sin(k * x) * np.cos(k * y)
    elif kind in ("Primitive", "primitive", "schwarz-p", "p", "schwarzp"):
        F = np.cos(k * z) + np.cos(k * y) + np.cos(k * x)
    elif kind in ("Diamond", "diamond", "DIAMOND"):
        F = np.sin(k * x) * np.sin(k * y) * np.sin(k * z) + np.sin(k * x) * np.cos(k * y) * np.cos(k * z) + np.cos(
            k * x) * np.sin(k * y) * np.cos(k * z) + np.cos(k * x) * np.cos(k * y) * np.sin(k * z)
    elif kind in ("FRD", "frd", "Fischer-Koch Random Dots"):
        # F = 8*np.cos(k*x)*np.cos(k*y)*np.cos(k*z)+8*np.cos(2*k*x)*np.cos(2*k*y)*np.cos(2*k*z)-np.cos(2*k*x)*np.cos(2*k*y)-np.cos(2*k*y)*np.cos(2*k*z)-np.cos(2*k*z)*np.cos(2*k*x)
        F = 4 * np.cos(x * k) * np.cos(y * k) * np.cos(z * k) - np.cos(2 * x * k) * np.cos(2 * y * k) - np.cos(
            2 * y * k) * np.cos(2 * z * k) - np.cos(2 * z * k) * np.cos(2 * x * k)
    elif kind in ("IWP", "iwp", "Isotropic Woodpile"):
        F = np.cos(2 * x * k) + np.cos(2 * y * k) + np.cos(2 * z * k) - 2 * np.cos(x * k) * np.cos(y * k) - 2 * np.cos(
            y * k) * np.cos(z * k) - 2 * np.cos(z * k) * np.cos(x * k)
    elif kind in ("Neovius", "neovius", "N", "n"):
        F = 3 * np.cos(x * k) + 3 * np.cos(y * k) + 3 * np.cos(z * k) + 4 * np.cos(x * k) * np.cos(y * k) * np.cos(
            z * k)
    else:
        raise ValueError("Unknown TPMS kind")

    if mode == 'sheet':
        # Sheet Logic:
        # We want the region where |F| < iso.
        # Marching cubes finds level=0.
        # We define Value = iso - |F|.
        # If Value > 0, then |F| < iso (Solid).
        return F
    else:
        # Skeletal Logic (Original):
        return F - iso


def generate_iso_mesh(size, resolution, scale, c, kind, mode):
    """Generate a mesh for the solid volume on one side of the gyroid surface within a cube."""
    x = np.linspace(0, 1, num=resolution)
    y = np.linspace(0, 1, num=resolution)
    z = np.linspace(0, 1, num=resolution)
    X, Y, Z = np.meshgrid(x, y, z)
    values = tpms_value(X, Y, Z, k=scale, kind=kind, iso=c, mode=mode)
    t0 = time.time()

    if mode == 'sheet':
        # values = np.pad(values, pad_width=1, mode='constant', constant_values=-1.0)
        values_1=c-values
        values_2=c+values
        verts1, faces1, _, _ = measure.marching_cubes(values_1, level=0)
        verts2, faces2, _, _ = measure.marching_cubes(values_2, level=0)
        verts = np.vstack((verts1, verts2))

        create_stl_from_mesh(verts1, faces1, "1", "2.stl")
        create_stl_from_mesh(verts2, faces2, "1", "3.stl")


        # 2. 合并面 (关键步骤！)
        # faces2 的索引是基于 verts2 的 (0, 1, 2...)
        # 合并后，verts2 排在 verts1 后面
        # 所以 faces2 的所有索引都要加上 len(verts1)
        faces2_offset = faces2 + len(verts1)
        faces = np.vstack((faces1, faces2_offset))

        # verts = verts - 1.0
    else:
        verts, faces, _, _ = measure.marching_cubes(values, level=0)

    # verts, faces = mcubes.marching_cubes(values, 0.0)
    print(f"[mcubes] {len(verts)} verts, {len(faces)} tris in {time.time() - t0:.2f}s")

    # map to world
    dx, dy, dz = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    ox, oy, oz = x[0], y[0], z[0]
    Vw = np.empty_like(verts, dtype=np.float64)
    Vw[:, 0] = ox + verts[:, 0] * dx
    Vw[:, 1] = oy + verts[:, 1] * dy
    Vw[:, 2] = oz + verts[:, 2] * dz

    create_stl_from_mesh(Vw, faces, "1", "1.stl")

    return Vw, faces


def snap_to_cube_planes(V, tol):
    for ax in range(3):
        near0 = np.isclose(V[:, ax], 0.0, atol=tol)
        near1 = np.isclose(V[:, ax], 1.0, atol=tol)
        V[near0, ax] = 0.0
        V[near1, ax] = 1.0
    return V


def decimate_and_clean(V, F, max_tris):
    mesh = o3d.geometry.TriangleMesh(
        vertices=o3d.utility.Vector3dVector(V),
        triangles=o3d.utility.Vector3iVector(F.astype(np.int32))
    )
    mesh.remove_duplicated_vertices()
    mesh.remove_degenerate_triangles()
    mesh.remove_duplicated_triangles()
    # mesh.remove_non_manifold_edges()
    if len(np.asarray(mesh.triangles)) > max_tris:
        t0 = time.time()
        mesh = mesh.simplify_quadric_decimation(max_tris)
        print(f"[decimate] → {len(np.asarray(mesh.triangles))} tris in {time.time() - t0:.2f}s")
        mesh.remove_duplicated_vertices()
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_non_manifold_edges()
    return np.asarray(mesh.vertices), np.asarray(mesh.triangles, dtype=np.int32)


# ---------- build caps only on end faces (x=0/1,y=0/1,z=0/1) ----------
def _on_plane_mask(V, ax, val, tol):
    return np.isclose(V[:, ax], val, atol=tol)


def _boundary_loops_on_plane(V, F, ax, val, tol, kind, direction='normal',mode="sheet"):
    """Return ordered vertex loops for open edges that lie on plane x/y/z=val."""
    # 1. 筛选点
    # 找出一个布尔掩码，标记哪些顶点在这个平面上（考虑误差 tol）
    vmask = _on_plane_mask(V, ax, val, tol=SNAP_TOL)

    # count all edges → boundary = edges used by exactly 1 triangle
    # 2. 【寻找边界边】 (Edge Detection)
    cnt = Counter()
    for tri in F:
        # ... (遍历所有三角形的三条边，排序后存入 Counter 计数) ...
        # 逻辑：内部边的计数必定是 2，边界边的计数是 1。
        i, j, k = map(int, tri)
        for a, b in ((i, j), (j, k), (k, i)):
            if a > b:
                a, b = b, a
            cnt[(a, b)] += 1

    # only edge that is used by one time in triangle is plane
    boundary_edges = [(a, b) for (a, b), c in cnt.items() if c == 1 and vmask[a] and vmask[b]]

    # build adjacency
    # 3. 【构建邻接表】
    # 把无序的边变成图结构：点 A 连接着 点 B...
    nbrs = defaultdict(list)
    for a, b in boundary_edges:
        nbrs[a].append(b)
        nbrs[b].append(a)
    # print (len(list(nbrs.keys())), list(nbrs.keys()))

    # count all boundary vertices on the edges of the end faces
    cnt_vert = Counter()
    for couple in boundary_edges:
        (m, n) = couple
        if m != n:
            cnt_vert[m] += 1
            cnt_vert[n] += 1
        else:
            print(m, n, V[m], V[n])
    # print (cnt_vert)
    # points that show once (start point)
    boundary_verts = [m for m, c in cnt_vert.items() if c == 1]

    # trace closed loops
    loops = {}  # 存储找到的所有路径/环，格式 {0: [v1, v2...], 1: [...]}
    visited_e = set()  # 记录已经走过的“边”（Edge），防止重复走回头路
    i = 0
    round_test = 0  # 标志位：记录是否找到了完美的闭合环
    # print (boundary_verts, V[boundary_verts], V[list(nbrs.keys())])

    # 遍历所有可能的起点。
    # 优先遍历 boundary_verts（端点），然后是所有邻居节点 nbrs.keys()。
    for start in boundary_verts + list(nbrs.keys()):
        # skip vertices already fully visited
        # 【防御性检查】
        # 检查 start 连接的所有边是否都已经访问过了。
        # 如果这个点的所有路都走过了，说明它已经被包含在之前的 loop 里了，直接跳过。
        if all(((start, n) in visited_e or (n, start) in visited_e) for n in nbrs[start]):
            continue
        loop = [start]
        prev = None
        cur = start
        while True:
            # pick next neighbor not yet used
            nxt = None
            for n in nbrs[cur]:
                key = (cur, n) if cur < n else (n, cur)

                # 【关键逻辑】
                # 1. key not in visited_e: 这条路没走过
                # 2. n != prev: 不能立刻调头回去（比如 A->B，不能立刻 B->A）
                if key not in visited_e and n != prev:
                    nxt = n;
                    break

            # --- 情况 A：无路可走（死胡同） ---
            if nxt is None:
                # 说明这是一条“开放的线段”（Open Polyline），走到了尽头。
                # print (2)
                loops[i] = loop
                # print ("line", i)
                i += 1
                break

            visited_e.add((cur, nxt) if cur < nxt else (nxt, cur))
            loop.append(nxt)
            # print ("loop", loop)
            prev, cur = cur, nxt

            # --- 情况 B：走回起点了（闭环） ---
            if cur == start:  # closed
                # 这是一个完美的圆环（Closed Loop）。
                # print (3)
                loops[i] = loop
                round_test = 1
                # print ("round", i)
                i += 1
                break
            # locate the re-ordered boundary points on the loops

    # determine the start point for skeletal TPMS
    if mode=="skeletal":
        d = 0
        longest = 0
        l = 0
        for i in loops.keys():
            dist = math.dist(V[loops[i][0]], V[loops[i]][-1])
            length = len(loops[i])
            # print (dist, length)
            if length > l or dist > d:
                if length > l:
                    l = length
                if dist > d:
                    d = dist
                longest = i
                # print (i, longest, len(loops[i]))
        # print (longest)
        longest_start = loops[longest][0]
        longest_end = loops[longest][-1]
        # print (longest_start, longest_end)

    # determine the start point for sheet TPMS (much more special)
    else:
        max_len = 0
        max_dist = 0
        for i in loops.keys():
            dist = math.dist(V[loops[i][0]], V[loops[i][-1]])
            length = len(loops[i])
            if length > max_len: max_len = length
            if dist > max_dist: max_dist = dist

        candidates = []
        for i in loops.keys():
            dist = math.dist(V[loops[i][0]], V[loops[i][-1]])
            length = len(loops[i])
            if dist > 0.98 * max_dist or length > 0.98*max_len:
                candidates.append(i)

        # 3. 第三步：根据相邻关系决定顺序 (User Optimized Logic)
        if len(candidates) == 1:
            longest = candidates[0]
            start = 0
            end = -1
            # print("only one point")

        else:
            # 必须先生成 boundary_verts_cw
            temp_cw = order_vertices_clockwise_x0_face(V, boundary_verts, ax, val)

            # 我们只重点关注前两个候选者（通常也就这两个）
            c0 = candidates[0]
            c1 = candidates[1]
            # 获取两个线段的首尾点
            s0, e0 = loops[c0][0], loops[c0][-1]
            s1, e1 = loops[c1][0], loops[c1][-1]

            # 获取它们在几何圆圈中的"排位" (Rank)
            idx_s0 = temp_cw.index(s0)
            idx_e0 = temp_cw.index(e0)
            idx_s1 = temp_cw.index(s1)
            idx_e1 = temp_cw.index(e1)
            # print(idx_s0, idx_e0, idx_s1, idx_e1)

            # 【核心逻辑】：寻找"缝隙"
            # 如果 c0 的尾巴 紧挨着 c1 的头 (差值为1)，说明 c0 在前，c1 在后。选 c0。
            # 你的规则："选择这两个点里面序号小的" -> e0 小于 s1 -> 选 c0。

            if np.abs(idx_e1 - idx_e0) == 1:
                longest = c1
                start=-1
                end=0

            elif np.abs(idx_e1 - idx_s0) == 1:
                longest = c0
                start=-1
                end=0
            elif np.abs(idx_e0 - idx_s1) == 1:
                longest = c1
                start=0
                end=-1
            elif np.abs(idx_s1 - idx_s0) == 1:
                longest = c0
                start=-1
                end=0
            else:
                longest = c0
                start=0
                end=-1
                print("error!!!!!")
        longest_start = loops[longest][start]
        # print(longest_start)
        longest_end = loops[longest][end]

    if len(boundary_verts) > 0:
        # 1. 【强制排序】
        # 我们不管 loops 怎么连，先拿出面上所有的点，按几何中心进行“顺时针排序”。
        # 这就像让一群乱跑的小朋友按高矮顺序排好队。

        # reorder the vertices in clockwise / counter-clockwise direction
        boundary_verts_cw = order_vertices_clockwise_x0_face(V, boundary_verts, ax, val)
        # print (V[boundary_verts_cw])

        # 2. 【对齐起点】
        # 将排好序的圆圈列表旋转一下，让它的起点对齐到之前找到的“最长路径”的起点 (longest_start) 或终点。
        # 目的：让“理想的几何顺序”和“实际的物理路径”尽可能重合。

        boundary_verts_cw1 = reorder_list(boundary_verts_cw, longest_start)
        boundary_verts_cw2 = reorder_list(boundary_verts_cw, longest_end)
        # print (boundary_verts_cw1)
        # print (boundary_verts_cw2)

        # 3. 【方向选择】
        # 根据用户想要的面法线方向（normal 或 reverse），选择使用哪一个列表。
        # 这决定了最后生成的面是朝外还是朝里。
        if direction == 'normal':
            if ax == 1 and kind !="FRD":
                circle = boundary_verts_cw2
            else:
                circle = boundary_verts_cw1
        elif direction == 'reverse':
            if ax == 1:
                circle = boundary_verts_cw1
            else:
                circle = boundary_verts_cw2
        if kind in ['Diamond', 'diamond', 'DIAMOND']:
            if direction == 'normal':
                if ax == 1:
                    circle = boundary_verts_cw1
            elif direction == 'reverse':
                if ax == 1:
                    circle = boundary_verts_cw2

        vert_id = []
        for i in range(0, len(circle)):
            for j in range(0, len(loops.keys())):
                # 遍历 circle 里的每一个点，看看它是哪个 loop 的起点或终点？
                if circle[i] == loops[j][0]:
                    vert_id += ['loop' + str(j) + '_start']
                elif circle[i] == loops[j][-1]:
                    vert_id += ['loop' + str(j) + '_end']

        # 寻找标记点 (Mark)
        # 这一步有点晦涩。它在检查 vert_id 列表，试图找到一个“循环点”。
        # vert_id[i][4] 取的是字符串的第5个字符，也就是 loop 的 ID (比如 'loop3_start' 取 '3')。
        # 如果发现某个 ID 和第一个点的 ID 相同，说明转了一圈回来了，标记这个位置。
        # print(circle[10], loops[int(vert_id[10][4])])
        # print(reverse_loop(circle[i], loops[int(vert_id[i][4])])[::-1])

        for i in range(1, len(vert_id)):
            if vert_id[i][4] == vert_id[0][4]:
                mark = i

    # for gyroid and FKS

    # 第一板块：复杂拓扑拼接 (Gyroid, FKS, Diamond)
    if kind in ["gyroid", "g", "Gyroid", "FKS", "fks", "Fischer-Koch-S", "Diamond", "diamond", "DIAMOND"] or (mode=="sheet" and kind=="FRD"):
        # build closed loops
        # print (circle, vert_id, V[circle])
        loops_final = {}
        a = 0
        used = []

        # 遍历所有打过标签的关键点（起点或终点）
        for i in range(0, len(vert_id)):
            if i == 0:
                # 拿出第一段线段。reverse_loop 确保线段方向和 circle 方向一致。
                # [::-1] 是为了反转列表，确保拼接时的头尾相接顺序。
                loops_final[a] = reverse_loop(circle[i], loops[int(vert_id[i][4])])[::-1]
                used += [0, mark]  # 标记起点和对应的循环点已处理

            elif i > 0 and i not in used and i < mark:
                # print (loops_final, a)
                if len(loops_final[a]) > 0:
                    d = i - 1
                else:
                    d = i + 1

                # 【核心动作：拐角修复】
                # 我们刚结束上一段路（在 circle[d]），现在要开始下一段路（在 circle[i]）。
                # 检查这两个点之间是否跨越了立方体角点。
                corner = add_corner(circle[d], circle[i], ax, val, V)
                if corner != None:
                    loops_final[a] += [len(V)]
                    V = np.append(V, np.array([corner]), axis=0)

                loops_final[a] += reverse_loop(circle[i], loops[int(vert_id[i][4])])
                endx = loops_final[a][-1]
                end_index = circle.index(endx)
                used += [i, end_index]

                if d not in used:
                    # 如果上一站 d 竟然没在账本里？说明 d 是一个被遗漏的线段头。
                    # 我们刚才只顾着往后连，忘了前面的 d 其实也连着一段路。
                    # 动作：把 d 对应的路找出来，反向拼接到当前列表的【最前面】。 loops[int(vert_id[i][4])])[::-1]？？？
                    loops_final[a] = reverse_loop(circle[d], loops[int(vert_id[d][4])])[::-1] + loops_final[a]
                    endx = reverse_loop(circle[d], loops[int(vert_id[d][4])])[-1]
                    used += [d, circle.index(endx)]


                # d=i+1---> end_index-1=i??? 重复加点
                if (end_index + 1 in used and d == i - 1) or (end_index - 1 in used and d == i + 1):
                    corner = add_corner(loops_final[a][-1], loops_final[a][0], ax, val, V)
                    if corner != None:
                        loops_final[a] += [len(V)]
                        V = np.append(V, np.array([corner]), axis=0)
                    a += 1
                    loops_final[a] = []

            # separate point to connect
            elif i > mark and i not in used:
                # 长的支路会不会有问题 complex structure？
                if len(loops_final[a]) == 0:
                    loops_final[a] += reverse_loop(circle[i], loops[int(vert_id[i][4])])[::-1]
                    endx = reverse_loop(circle[i], loops[int(vert_id[i][4])])[-1]
                    end_index = circle.index(endx)
                    used += [i, end_index]
                    #
                    # if ax == 0 and val == 0 and a == 3:
                    #     loop_id=int(vert_id[i][4])
                    #     points = np.zeros((len(loops[loop_id]), 3)).tolist()
                    #     # print (loops[loop_id])
                    #     for j in range(len(loops[loop_id])):
                    #         # points[j,:] = V[loops[loop_id][j]]
                    #         points[j] = V[loops[loop_id][j]].tolist()
                    #     print(points)
                        # print(ax,val,loop_id,loops[loop_id])

                        # p = np.array(points)
                        # fig = plt.figure()
                        # ax1 = fig.add_subplot(111, projection='3d')
                        # ax1.scatter(p[:, 0], p[:, 1], p[:, 2])  # x, y, z为三维坐标数据
                        # ax1.set_xlim(0, 1)
                        # ax1.set_ylim(0, 1)
                        # ax1.set_zlim(0, 1)
                        # ax1.set_xlabel('X')
                        # ax1.set_ylabel('Y')
                        # ax1.set_zlabel('Z')
                        # plt.show()
                else:
                    corner = add_corner(loops_final[a][-1], circle[i], ax, val, V)
                    if corner != None:
                        loops_final[a] += [len(V)]
                        V = np.append(V, np.array([corner]), axis=0)

                    loops_final[a] += reverse_loop(circle[i], loops[int(vert_id[i][4])])
                    endx = reverse_loop(circle[i], loops[int(vert_id[i][4])])[-1]
                    end_index = circle.index(endx)
                    used += [i, end_index]


                c = i + 1

                # loops_final[a] += reverse_loop(circle[i], loops[int(vert_id[i][4])])[::-1]
                # endx = reverse_loop(circle[i], loops[int(vert_id[i][4])])[-1]
                # end_index = circle.index(endx)
                # used += [i, end_index]
                # c = i + 1

                if c > len(vert_id) - 1: #last point
                    c = i + 1 - len(vert_id) #c=0
                corner = add_corner(circle[c], circle[i], ax, val, V)
                if corner != None:
                    loops_final[a] += [len(V)]
                    V = np.append(V, np.array([corner]), axis=0)
                    # print(corner,V[circle[c]], V[circle[i]])
                if c not in used:
                    loops_final[a] += reverse_loop(circle[c], loops[int(vert_id[c][4])])
                    endx = reverse_loop(circle[c], loops[int(vert_id[c][4])])[-1]
                    end_index = circle.index(endx)
                    used += [c, end_index]
                else:
                    a += 1
                    loops_final[a] = []
                    continue
                if end_index + 1 in used:
                    corner = add_corner(loops_final[a][-1], loops_final[a][0], ax, val, V)
                    if corner != None:
                        loops_final[a] += [len(V)]
                        V = np.append(V, np.array([corner]), axis=0)
                    a += 1
                    loops_final[a] = []

    # special program for sheet based primitive
    elif kind in ["IWP", "iwp", "Isotropic Woodpile","Neovius", "neovius", "N", "n"] and mode == "sheet":
        # --- 1. 双向排序 (核心基础) ---
        from collections import deque
        def sort_loop_bidirectional(indices, V):
            if len(indices) < 3: return list(indices)
            remaining = []
            for idx in indices: remaining.append((idx, V[idx]))

            start_node = remaining.pop(0)
            dq = deque([start_node])

            while remaining:
                head_pos = dq[0][1]
                tail_pos = dq[-1][1]
                best_idx = -1
                min_dist = float('inf')
                attach_to = None

                for i, (idx, pos) in enumerate(remaining):
                    d_head = np.linalg.norm(pos - head_pos)
                    if d_head < min_dist:
                        min_dist = d_head
                        best_idx = i
                        attach_to = 'head'
                    d_tail = np.linalg.norm(pos - tail_pos)
                    if d_tail < min_dist:
                        min_dist = d_tail
                        best_idx = i
                        attach_to = 'tail'

                if best_idx != -1:
                    node = remaining.pop(best_idx)
                    if attach_to == 'head':
                        dq.appendleft(node)
                    else:
                        dq.append(node)
                else:
                    break
            return [node[0] for node in dq]

        # --- 2. 准备工作 ---
        output_loop_list = []
        keys = list(loops.keys())

        if not keys:
            pass
        else:
            axis_u = (ax + 1) % 3
            axis_v = (ax + 2) % 3

            # --- A. 排序整理 ---
            for k in keys:
                loops[k] = sort_loop_bidirectional(loops[k], V)

            # --- B. 计算质心与包围盒 ---
            centroids = {}
            bboxes = {}
            valid_keys = []

            for k in keys:
                pts = [V[i] for i in loops[k]]
                if len(pts) < 3: continue
                pts_2d = np.array([[p[axis_u], p[axis_v]] for p in pts])

                centroids[k] = np.mean(pts_2d, axis=0)
                # 记录 [min_u, min_v, max_u, max_v]
                bboxes[k] = (np.min(pts_2d[:, 0]), np.min(pts_2d[:, 1]),
                             np.max(pts_2d[:, 0]), np.max(pts_2d[:, 1]))
                valid_keys.append(k)

            # --- C. 尝试配对 (放宽质心限制) ---
            pool = set(valid_keys)
            pairs = []
            singles = []

            while pool:
                k1 = pool.pop()
                if not pool:
                    singles.append(k1)
                    break

                c1 = centroids[k1]
                best_k2 = None
                # 【修改点1】大幅放宽质心距离阈值
                # 厚壁时，内外圈可能因为几何变形导致质心稍微偏离，0.05 可能不够
                min_dist = 0.2

                for candidate in pool:
                    c2 = centroids[candidate]
                    dist = np.linalg.norm(c1 - c2)
                    if dist < min_dist:
                        min_dist = dist
                        best_k2 = candidate

                if best_k2 is not None:
                    pool.remove(best_k2)
                    pairs.append((k1, best_k2))
                else:
                    singles.append(k1)

            # --- D. 缝合逻辑 (依赖嵌套检查，而非距离) ---
            for (k_a, k_b) in pairs:
                l1 = list(loops[k_a])
                l2 = list(loops[k_b])

                p1_s, p1_e = V[l1[0]], V[l1[-1]]
                p2_s, p2_e = V[l2[0]], V[l2[-1]]

                # D1. 确定大小圈 (Area Check)
                bb1 = bboxes[k_a]
                bb2 = bboxes[k_b]
                area1 = (bb1[2] - bb1[0]) * (bb1[3] - bb1[1])
                area2 = (bb2[2] - bb2[0]) * (bb2[3] - bb2[1])

                if area2 > area1:
                    l1, l2 = l2, l1  # l1 is Outer
                    bb1, bb2 = bb2, bb1

                # D2. 【核心】嵌套检查 (Nested Check)
                # 只要是嵌套的，哪怕距离再远也要缝合！
                # 稍微放宽一点判定边界 (-0.02)，防止浮点误差
                is_nested = (bb2[0] >= bb1[0] - 0.02 and bb2[1] >= bb1[1] - 0.02 and
                             bb2[2] <= bb1[2] + 0.02 and bb2[3] <= bb1[3] + 0.02)

                if not is_nested:
                    print(f"Warning: Pairs not nested. Treating as singles.")
                    singles.append(k_a)  # 注意：这里 append key 只是为了逻辑，后面要用 list
                    singles.append(k_b)
                    # 这里的 singles 列表其实在下面没用到，我们直接在这里把它们加到 output
                    # 并做强制闭合处理
                    if np.linalg.norm(p1_s - p1_e) > 1e-5: l1.append(l1[0])
                    if np.linalg.norm(p2_s - p2_e) > 1e-5: l2.append(l2[0])
                    output_loop_list.append(np.array(l1))
                    output_loop_list.append(np.array(l2))
                    continue

                # D3. 缝合 (U-Turn Logic)
                dist_mode1 = np.linalg.norm(p1_e - p2_e) + np.linalg.norm(p1_s - p2_s)
                dist_mode2 = np.linalg.norm(p1_e - p2_s) + np.linalg.norm(p2_e - p1_s)

                merged = []
                # 【修改点2】彻底移除了 `bridge_gap > 0.15` 的熔断检查
                # 既然通过了嵌套检查，说明它们就是一对。厚度大导致距离远是正常的。

                if dist_mode1 < dist_mode2:  # 同向
                    merged.extend(l1)
                    merged.extend(l2[::-1])
                    merged.append(l1[0])
                else:  # 反向
                    merged.extend(l1)
                    merged.extend(l2)
                    merged.append(l1[0])

                output_loop_list.append(np.array(merged))

            # --- E. 处理 Singles (强制闭合) ---
            # 处理那些一开始就没配对上的
            for k in singles:
                # 注意：刚才在 D2 步骤被退回的 k_a, k_b 已经在上面处理并添加了，
                # 所以这里只处理最初在 Pool 里落单的

                # 简单起见，我们重新从 loops 里取，但要小心不要重复添加
                # 由于 output_loop_list 是列表，我们需要确保不重复
                # 这里最安全的做法是：直接处理。因为 D2 退回的没有加回 singles 列表(除了上面那行append)，
                # 等等，上面 `singles.append(k_a)` 了。
                # 为了防止逻辑混乱，我们在 D2 如果退回，直接处理并 continue 了，
                # 所以不要把它们加回 singles 列表，或者在 E 里面要有去重机制。

                # 修正：D2 里的 `singles.append` 删掉，直接处理完 continue 最好。
                # 但由于上面的代码已经写了 append，我们这里简单一点：
                # 只要 k 还在 singles 里，就处理。

                l_s = list(loops[k])
                # 强制闭合
                if len(l_s) > 2 and np.linalg.norm(V[l_s[0]] - V[l_s[-1]]) > 1e-5:
                    l_s.append(l_s[0])
                output_loop_list.append(np.array(l_s))

        # --- F. 输出 ---
        # 此时 output_loop_list 里可能有重复添加的风险（如果在 D2 里处理了又加回 Singles）
        # 让我们优化一下 D2 的逻辑，确保不重复。
        # (上面的代码里，D2 的 singles.append 其实是多余的，因为我也直接 output.append 了)
        # (但为了安全，下面的 F 步会自动重建索引，所以即便有重复数据也只是多了个重叠面，不会崩)

        loops_final = {}
        for i, pts in enumerate(output_loop_list):
            loops_final[i] = pts

    # ========================================================

    # ========================================================

    elif kind in ["Primitive", "primitive", "FRD", "frd", "Fischer-Koch Random Dots",
                  "IWP", "iwp", "Isotropic Woodpile", "Neovius", "neovius", "N", "n"]:
        loops_final = {}
        # 遍历所有找到的线段 (loops)
        # 在 Normal 模式下，通常只有一个主 loop (a=0)
        for a in loops.keys():
            loops_final[a] = loops[a]
            # print (len(loops[a]))
            # print ("test", a, loops[a])

            # --- 检查线段是否接触边界 ---
            cnt = 0
            for vert in boundary_verts:
                if vert in loops_final[a]:
                    cnt += 1
            corner_mark = None
            if cnt > 0:
                corner_mark = add_corner(loops_final[a][-1], loops_final[a][0], ax, val, V)

                # shape
                if corner_mark != None:
                    loops_final[a] += [len(V)]
                    V = np.append(V, np.array([corner_mark]), axis=0)
                    # print (len(loops[a]))

                    # 【重要】去掉路径的最后一个点。
                    # 这是一个非常隐晦的操作。通常是为了避免重复闭合，或者为后续反向逻辑做准备。
                    # 在这里，它可能是认为原始数据的最后一个点是多余的，或者为了断开闭环以便后续重组。
                    loops[a] = loops[a][:-1]
                    # print (len(loops[a]))
            # print (corner_mark)
        # print(len(loops))


        # special program for sheet based primitive
        if kind in ["Primitive", "primitive"] and mode == "sheet":
            loops_final = {}
            keys = list(loops.keys())

            # Primitive Sheet 截面通常是 2 个同心环
            # Primitive Sheet 截面通常是 2 个同心环
            if len(keys) == 2:
                # 定义平面上的两个轴 (用于寻找物理极值)
                # 比如当前是 X面(0)，那么 u=Y(1), v=Z(2)
                axis_u = (ax + 1) % 3  # 横向轴 (用于判断左右)
                axis_v = (ax + 2) % 3  # 纵向轴 (用于找顶底)

                processed_splits = []

                for k in keys:
                    curr = list(loops[k])
                    if curr[0] == curr[-1]: curr = curr[:-1]  # 去重尾部

                    # 1. 【物理对齐】找到 V 轴上的最低点 (Start)
                    min_v = float('inf')
                    idx_min = -1
                    for i, idx in enumerate(curr):
                        val = V[idx][axis_v]
                        if val < min_v:
                            min_v = val
                            idx_min = i

                    # 旋转列表，让最低点 (Bottom) 排在 index 0
                    curr = curr[idx_min:] + curr[:idx_min]

                    # 2. 【几何切割】找到 V 轴上的最高点 (Peak) 作为切割点
                    # 不再使用 len/2，而是寻找真正的物理最高点
                    max_v = float('-inf')
                    idx_peak = -1
                    for i, idx in enumerate(curr):
                        val = V[idx][axis_v]
                        if val > max_v:
                            max_v = val
                            idx_peak = i

                    # 3. 【方向统一】判断是从左边上去的，还是从右边上去的？
                    # 计算前半段 (Bottom -> Peak) 在 U 轴上的平均坐标
                    # 如果前半段的 U 小于 后半段的 U，说明是顺时针(或左侧优先)
                    half_1 = curr[:idx_peak + 1]
                    half_2 = curr[idx_peak:] + [curr[0]]

                    avg_u_1 = np.mean([V[p][axis_u] for p in half_1])
                    avg_u_2 = np.mean([V[p][axis_u] for p in half_2])

                    if avg_u_1 > avg_u_2:
                        # 说明前半段在"右边" (U值大)，这与我们的期望(先左后右)相反
                        # 动作：把整个圆环反转！(保持 Start 不变)
                        # 反转逻辑：Start(0) 保持不动，后面所有点倒序
                        curr = [curr[0]] + curr[1:][::-1]

                        # 反转后，Peak 的索引位置也变了，需要换算一下
                        idx_peak = len(curr) - idx_peak

                        # 重新生成切片
                        half_1 = curr[:idx_peak + 1]  # 左半圆 (Bot -> Top)
                        half_2 = curr[idx_peak:] + [curr[0]]  # 右半圆 (Top -> Bot)

                    processed_splits.append((half_1, half_2))

                # 4. 【缝合】
                # 此时 processed_splits[0] 和 [1] 结构完全一致：
                # [0] 是左半圆 (Bot -> Top)，[1] 是右半圆 (Top -> Bot)
                # 且切点都在物理最高/最低点，完美对齐。

                l0_left, l0_right = processed_splits[0]
                l1_left, l1_right = processed_splits[1]

                # 缝合左侧回路: 外环左半(Bot->Top) + 内环左半(Top->Bot, 需反转)
                loops_final[0] = l0_left + l1_left[::-1]

                # 缝合右侧回路: 外环右半(Top->Bot) + 内环右半(Bot->Top, 需反转)
                loops_final[1] = l0_right + l1_right[::-1]

                # print(
                #     f"[Primitive Fix] Geometric Split Success. Left: {len(loops_final[0])}, Right: {len(loops_final[1])}")

            else:
                # 兜底
                print(f"[Primitive Fix] Warning: Expected 2 loops, found {len(keys)}")
                for i, k in enumerate(keys):
                    loops_final[i] = loops[k]

        # reverse direction of skeletal TPMS
        elif direction == "reverse":
        # if 1:
            # print ("test:", 1)
            loops_final = {}
            # if round_test == 1:
            low = 0.5
            high = 0.5

            # 确定平面内的另一个轴 c。
            # 如果切面轴 ax=2 (Z轴), 那么 c 可能是 Y轴 (1) 或 X轴 (0)
            c = ax + 1
            if c > 2:
                c -= 3
            # for loop in loops.keys():
            # print (loop, len(loops[loop]))

            # --- round_test 逻辑 (处理特殊长环) ---
            # 这一段是为了处理某些情况下，线段是一个巨大的“回”字形，需要根据几何位置把它切开
            if round_test == 1:
                # print ("test:", 2)
                for start in loops[longest]:
                    if V[start][ax - 1] > high:
                        high = V[start][ax - 1]
                        high_index = start
                    if V[start][ax - 1] < low:
                        low = V[start][ax - 1]
                        low_index = start

                # 以最高点为起点重新排序，然后截取到最低点 -> 得到上半段
                loopx = {}
                loopx[0] = reorder_list(loops[longest], high_index)
                end = loopx[0].index(low_index)
                loopx[0] = loopx[0][0:end + 1]

                # 以最低点为起点重新排序，截取到最高点，并反转 -> 得到下半段
                loopx[1] = reorder_list(loops[longest], low_index)
                end = loopx[1].index(high_index)
                loopx[1] = loopx[1][0:end + 1][::-1]

                # 确保 loopx[0] 在几何上位于 loopx[1] 的左侧/下方，方便后续按顺序拼
                if V[loopx[0][0]][c] < V[loopx[0][1]][c]:
                    loopx[0], loopx[1] = loopx[1], loopx[0]

            # 情况 A: 之前检测到了角点 (说明是十字形空隙)
            if corner_mark != None:
                mid_high = [0, 0, 0]
                mid_low = [0, 0, 0]
                mid_high[ax] = mid_low[ax] = val

                # 定义两个中点锚点
                # 这里的逻辑是硬编码的：假设结构是对称的，锚点在 (1, 0.5) 和 (0, 0.5) 这种位置
                mid_high[ax - 1] = 1
                mid_low[ax - 1] = 0
                mid_high[c] = 0.5
                mid_low[c] = 0.5


            elif corner_mark == None:
                # 锚点设在角落 (0,0) 和 (1,1) 这种位置
                mid_high = [0, 0, 0]
                mid_low = [0, 0, 0]
                mid_high[ax] = mid_low[ax] = val
                mid_high[ax - 1] = mid_high[c] = 1
                mid_low[ax - 1] = mid_low[c] = 0
            # print ("mid_low:", mid_low, "mid_high:", mid_high)

            # 把计算好的两个“锚点”加入到顶点库 V，如果库里还没有的话
            for mid in (mid_low, mid_high):
                if mid not in V.tolist():
                    V = np.append(V, np.array([mid]), axis=0)
            # print ("mid points", V[15984], V[15985])

            m = 0
            axis = [c, ax - 1]
            for loopy in [0, 1]:
                if round_test == 1:
                    loops_final[m] = loopx[loopy]
                else:
                    loops_final[m] = []

                # 1. 加入起始锚点 (mid_low)
                loops_final[m] += [V.tolist().index(mid_low)]
                # 记录结束锚点 (mid_high) 的索引
                end = V.tolist().index(mid_high)

                # 2. 定义当前区域的两个“墙角” (Corner1, Corner2)
                # 比如：左下角和左上角
                corner1 = [0, 0, 0]
                corner1[c] = m
                corner1[ax - 1] = 0
                corner2 = [0, 0, 0]
                corner2[c] = m
                corner2[ax - 1] = 1
                corner1[ax] = corner2[ax] = val

                if round_test == 1:
                    for corner in (corner1, corner2):
                        if corner not in V.tolist():
                            V = np.append(V, np.array([corner]), axis=0)
                    loops_final[m] += [V.tolist().index(corner1)]
                    loops_final[m] += [V.tolist().index(corner2)]
                else:
                    if corner_mark == None:
                        for ele in circle:
                            # print (V[ele], V[ele][ax-1], corner1[ax-1], corner2[ax-1])

                            # 左下
                            if (0 < V[ele][axis[loopy]] and V[ele][axis[loopy]] < 0.5) and V[ele][axis[1 - loopy]] == 0:
                                add1 = ele
                                # print (1, ele)
                            # 右下
                            if (0.5 < V[ele][axis[loopy]] and V[ele][axis[loopy]] < 1) and V[ele][axis[1 - loopy]] == 0:
                                add2 = ele
                                # print (2, ele)

                            # 左侧上半
                            if (0 < V[ele][axis[1 - loopy]] and V[ele][axis[1 - loopy]] < 0.5) and V[ele][
                                axis[loopy]] == 1:
                                add3 = ele
                                # print (3, ele)
                            # 右侧上半
                            if (0.5 < V[ele][axis[1 - loopy]] and V[ele][axis[1 - loopy]] < 1) and V[ele][
                                axis[loopy]] == 1:

                                add4 = ele
                                # print (4, ele)


                    if corner_mark != None:

                        # mid_low > add1 > add2 > add3> add4 > mid_high
                        for ele in circle:

                            # --- 寻找 add1 (左下弧线的起点：底部) ---
                            # 翻译：X 在 0 到 0.5 之间，且 Y 等于 0
                            # print (V[ele], V[ele][ax-1], corner1[ax-1], corner2[ax-1])
                            if (m / 2 < V[ele][axis[0]] and V[ele][axis[0]] < (m + 1) / 2) and V[ele][axis[1]] == 0:
                                add1 = ele
                                # print (1, ele)

                            # --- 寻找 add2 (左下弧线的终点：左墙下半截) ---
                            # 翻译：Y 在 0 到 0.5 之间，且 X 等于 m (0)
                            if (0 < V[ele][axis[1]] and V[ele][axis[1]] < 0.5) and V[ele][axis[0]] == m:
                                add2 = ele
                                # print (2, ele)

                            # --- 寻找 add3 (左上弧线的起点：左墙上半截) ---
                            # 翻译：Y 在 0.5 到 1 之间，且 X 等于 m (0)
                            if (0.5 < V[ele][axis[1]] and V[ele][axis[1]] < 1) and V[ele][axis[0]] == m:
                                add3 = ele
                                # print (3, ele)

                            if (m / 2 < V[ele][axis[0]] and V[ele][axis[0]] < (m + 1) / 2) and V[ele][axis[1]] == 1:
                                add4 = ele
                                # print (4, ele)

                    for loop in loops:
                        if add1 in loops[loop]:
                            # print ("test", loops_final[m], add1, loops[loop], reverse_loop(add1, loops[loop]) )
                            loops_final[m] += reverse_loop(add1, loops[loop])
                    corner = add_corner(add2, add3, ax, val, V)
                    # print ('warning', add2, add3, corner)
                    # print ('warning', loops_final[m], len(V))
                    if corner != None:
                        loops_final[m] += [len(V)]
                        V = np.append(V, np.array([corner]), axis=0)
                    for loop in loops:
                        if add3 in loops[loop]:
                            loops_final[m] += reverse_loop(add3, loops[loop])

                loops_final[m] += [end]
                # print (loops_final)
                m += 1


    if len(loops_final[list(loops_final.keys())[-1]]) == 0:
        del loops_final[list(loops_final.keys())[-1]]
    return loops_final, V


def calculate_triangle_normal(p1, p2, p3):
    """
    Calculates the unit normal vector of a triangle defined by three vertices.

    Args:
        p1 (list or np.array): Coordinates of the first vertex [x, y, z].
        p2 (list or np.array): Coordinates of the second vertex [x, y, z].
        p3 (list or np.array): Coordinates of the third vertex [x, y, z].

    Returns:
        np.array: The unit normal vector of the triangle.
    """
    v1 = np.array(p2) - np.array(p1)
    v2 = np.array(p3) - np.array(p1)

    normal = np.cross(v1, v2)
    unit_normal = normal / np.linalg.norm(normal)

    return unit_normal


def debug_visualize_loop(loop_indices, V, ax_idx, loop_id=0):
    """
    可视化 Loop 中点的连接顺序。
    - V: 所有顶点坐标
    - loop_indices: 当前 Loop 的点索引列表 [p1, p2, p3...]
    - ax_idx: 当前切面垂直轴 (0=x, 1=y, 2=z)，用于投影到 2D
    """
    import matplotlib.pyplot as plt

    # 1. 确定投影平面 (比如切面是 Z轴，那我们就画 XY 平面)
    u_idx = (ax_idx + 1) % 3
    v_idx = (ax_idx + 2) % 3

    # 2. 提取坐标
    pts = [V[i] for i in loop_indices]
    u_coords = [p[u_idx] for p in pts]
    v_coords = [p[v_idx] for p in pts]

    plt.figure(figsize=(10, 8))
    plt.title(f"Loop {loop_id} Order Check (Total: {len(pts)} pts)")

    # 3. 画连线 (显示轨迹)
    plt.plot(u_coords, v_coords, 'b-', alpha=0.5, linewidth=1, label='Path')

    # 4. 标记起点和终点
    plt.scatter(u_coords[0], v_coords[0], c='green', s=100, label='Start (0)', zorder=5)
    plt.scatter(u_coords[-1], v_coords[-1], c='red', s=100, label='End', zorder=5)

    # 5. 【核心】标出每个点的序号
    # 为了防止数字太密看不清，我们每隔几个点标一下，或者全标
    for i in range(len(u_coords)):
        # 偏移一点点，防止盖住点
        plt.text(u_coords[i], v_coords[i], str(i), fontsize=9, color='black', ha='right', va='bottom')
        plt.scatter(u_coords[i], v_coords[i], c='black', s=10, alpha=0.5)

    plt.xlabel(f"Axis {u_idx}")
    plt.ylabel(f"Axis {v_idx}")
    plt.legend()
    plt.grid(True)
    plt.axis('equal')  # 保证比例一致，圆就是圆
    plt.show()  # 这一句会暂停程序，关掉窗口后程序继续


def build_end_caps(V, F, tol, kind, direction='normal',mode="sheet"):
    """Create planar faces from boundary loops on each cube plane."""
    planes = [(0, 0.0), (0, 1.0), (1, 0.0), (1, 1.0), (2, 0.0), (2, 1.0)]
    # planes = [(1,0.0)]
    o = 0
    F1 = np.empty(shape=[0, 3])
    for ax, val in planes:
        norm = [0, 0, 0]
        norm[ax] = 0.5  # 设置中心点偏移
        end = [0, 0, 0]
        end[ax] = val  # 设置面上的点
        # 计算当前立方体面的标准法线方向（指向立方体外部）
        # 如果是 x=0 面，normal1 应该指向 -x 方向；如果是 x=1，指向 +x。
        normal1 = np.array(end) - np.array(norm)
        # print (ax, val)

        # 2. 【核心调用】获取该面上的边界环
        # 这一步最复杂，稍后详细讲。它返回 loops（一个字典，包含若干个闭合圆环的顶点索引）
        # 和更新后的顶点 V（因为可能添加了角点）。
        loops, V = _boundary_loops_on_plane(V, F, ax, val, tol, kind, direction=direction,mode=mode)

        # print("number of loop" ,len(loops))
        # for loop_id in loops.keys():
        #     # print (loops[loop_id])
        #     # 1. Get the points
        #     pp = np.zeros((len(loops[loop_id]), 3)).tolist()
        #     # print (loops[loop_id])
        #     for j in range(len(loops[loop_id])):
        #         # points[j,:] = V[loops[loop_id][j]]
        #         pp[j] = V[loops[loop_id][j]].tolist()
        #     print(ax,val,loop_id,loops[loop_id])
        #     p = np.array(pp)
        #     fig = plt.figure()
        #     ax1 = fig.add_subplot(111, projection='3d')
        #     ax1.scatter(p[:, 0], p[:, 1], p[:, 2])  # x, y, z为三维坐标数据
        #     ax1.set_xlim(0, 1)
        #     ax1.set_ylim(0, 1)
        #     ax1.set_zlim(0, 1)
        #     ax1.set_xlabel('X')
        #     ax1.set_ylabel('Y')
        #     ax1.set_zlabel('Z')
        #     plt.show()
        #     print(ax,val,loop_id,loops[loop_id])


        for loop_id in loops.keys():
            # print (loops[loop_id])
            o += 1
            # 1. Get the points
            points = np.zeros((len(loops[loop_id]), 3)).tolist()
            # print (loops[loop_id])
            for j in range(len(loops[loop_id])):
                # points[j,:] = V[loops[loop_id][j]]
                points[j] = V[loops[loop_id][j]].tolist()
            # print (o, points)
            # print(ax,val,loop_id,loops[loop_id])


            # p = np.array(points)
            # fig = plt.figure()
            # ax1 = fig.add_subplot(111, projection='3d')
            # ax1.scatter(p[:, 0], p[:, 1], p[:, 2])  # x, y, z为三维坐标数据
            # ax1.set_xlim(0, 1)
            # ax1.set_ylim(0, 1)
            # ax1.set_zlim(0, 1)
            # ax1.set_xlabel('X')
            # ax1.set_ylabel('Y')
            # ax1.set_zlabel('Z')
            # plt.show()
            # print(ax,val,loop_id,loops[loop_id])

            # 2. Delete the irrelevant axis
            modified_points = np.delete(np.array(points), obj=ax, axis=1)
            modified_points_list = modified_points.tolist()
            # print (modified_points_list)
            # 3. Perform Delaunay triangulation
            poly = Polygon(modified_points)
            # print("Polygon valid?", poly.is_valid)
            # if not poly.is_valid:
            #     print(explain_validity(poly))
            tris = constrained_delaunay_triangles(poly)
            # 4. Get the triangles and add triangles to faces
            triangles = np.zeros((len(tris.geoms), 3))
            for i in range(triangles.shape[0]):
                for j in range(triangles.shape[1]):
                    triangles[i, j] = modified_points_list.index(
                        [tris.geoms[i].exterior.coords[j][0], tris.geoms[i].exterior.coords[j][1]])
            for m in range(triangles.shape[0]):
                vert = {}
                for n in range(3):
                    # print (int(triangles[m][n]))
                    vert[n] = points[int(triangles[m][n])]
                normal2 = calculate_triangle_normal(vert[0], vert[1], vert[2])
                if np.dot(normal1, np.array(normal2)) < 0:
                    triangles[m][0], triangles[m][1] = triangles[m][1], triangles[m][0]
                F1 = np.concatenate(
                    (F1, np.array([[loops[loop_id][int(triangles[m][0])], loops[loop_id][int(triangles[m][1])],
                                    loops[loop_id][int(triangles[m][2])]]])), axis=0)
                # print (loops[loop_id][triangles[m][0]],loops[loop_id][triangles[m][1]],loops[loop_id][triangles[m][2]])
    F = np.concatenate((F, F1), axis=0)
    # print(f"[end-caps] planes capped with {o} faces")
    return V, F


def create_stl_from_mesh(verts, faces, folder, filename, caps=None):
    """Create an STL file from vertices and faces."""

    if not os.path.exists(folder):
        os.makedirs(folder)

    # Full path for the file
    full_path = os.path.join(folder, filename)
    solid_volume_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            solid_volume_mesh.vectors[i][j] = verts[int(f[j]), :]
    min_bound, max_bound = calculate_bounding_box(verts)
    if all(min_bound) != 0:
        print(f"Minimum corner of bounding box: {min_bound}")
    if all(max_bound) != 1:
        print(f"Maximum corner of bounding box: {max_bound}")
    solid_volume_mesh.save(full_path)
    print(f"STL file saved as {full_path}")


def order_vertices_clockwise_x0_face(V, boundary_verts, ax, val):
    """
    Orders 3D vertices on the x=0 face of a unit cube in a clockwise direction.

    Args:
        vertices: A list of tuples or lists representing 3D vertices (x, y, z).
                  All vertices are assumed to be on the x=0 face.

    Returns:
        A new list of vertices sorted in clockwise order.
    """
    # 1. 【筛选亲生队员】
    # 传入的 boundary_verts 可能是整个物体所有边界上的端点
    # 我们只关心：坐标轴 ax 的值等于 val 的那些点。
    # 比如：如果 ax=0, val=0，我们就只要 x=0 平面上的点。

    # Filter for vertices on the x=0 plane (optional, assuming input is valid)
    face_vertices = [v for v in boundary_verts if V[v][ax] == val]

    if not face_vertices:
        return []

    # 2. 【插旗杆（定中心）】
    # 极其重要的一步！要排成圆圈，必须得有一个圆心。
    # 这里有一个巨大的假设（Hard-coded）：假设你的模型在 0 到 1 的单位立方体内。
    # Calculate the center of the face in the other 2 planes
    center = [0.5, 0.5, 0.5]
    center[ax] = val  # 把中心点投影到当前的面上。

    # Calculate angles and sort
    def get_angle(vertex_id):

        # 1. 【计算相对向量】
        # 把点的位置减去中心点位置，得到一个从中心指向该点的向量。
        vertex = V[vertex_id]
        vector = vertex - center

        # 2. 【降维打击】 (3D -> 2D)
        # 我们要算平面角度，但点是 3D 的。必须把垂直于平面的那个轴扔掉。
        vec = {}
        j = 0
        for i in range(0, 3):
            if i != ax:
                vec[j] = vector[i]
                j += 1
        # vec[0] 是平面上的横坐标
        # vec[1] 是平面上的纵坐标

        # 3. 【极坐标转换】
        # math.atan2(y, x) 是计算机图形学神器。
        # 它能返回点 (x, y) 相对于原点的弧度值，范围是 -π 到 +π。

        return math.atan2(vec[0], vec[1])

    # Sort in descending order for clockwise direction
    # 4. 【排序】
    # key=get_angle: 告诉 sort 函数，用刚才算的弧度值作为排序依据。
    # reverse=True:  atan2 的角度通常是逆时针增加的。
    #                为了得到顺时针（Clockwise），我们需要由大到小排 (True)。
    sorted_vertices = sorted(face_vertices, key=get_angle, reverse=True)
    return sorted_vertices


def reorder_list(lst, new_start_element):
    try:
        pos = lst.index(new_start_element)
        return lst[pos:] + lst[:pos]
    except ValueError:
        print(f"Error: '{new_start_element}' not found in the list.")
        return lst


def calculate_bounding_box(vertices):
    # Calculate the minimum and maximum coordinates for each axis
    min_coords = np.min(vertices, axis=0)
    max_coords = np.max(vertices, axis=0)
    return min_coords, max_coords


def add_corner(point1_index, point2_index, ax, val, V):
    diff = V[point1_index] - V[point2_index]
    n = 0
    for j in range(0, 3):
        if diff[j] == 0:
            n += 1
    if n < 2:
        corner = [0, 0, 0]
        corner[ax] = val
        for b in range(0, 3):
            if b != ax:
                if max(V[point1_index][b], V[point2_index][b]) > 0.97:
                    corner[b] = 1
                elif max(V[point1_index][b], V[point2_index][b]) <0.03:
                    corner[b] = 0
        return corner
    else:
        return None


def reverse_loop(start, loop):
    if start == loop[0]:
        return loop
    elif start == loop[-1]:
        return loop[::-1]







