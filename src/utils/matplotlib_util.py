import numpy as np
import matplotlib.pyplot as plt
from utils.astropy_util import get_body_position
from utils.constants import BodyEnum, R_EARTH, R_MOON


class Plot:
    def __init__(self, df):
        self.fig = plt.figure()
        self.ax_2d = plt.subplot(121)
        self.ax = plt.subplot(122, projection="3d")

        self.ax.set_xlim(-10000000, 10000000)
        self.ax.set_ylim(-10000000, 10000000)
        self.ax.set_zlim(-10000000, 10000000)
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.set_zlabel("z")

        self.ax_2d.set_xlim(-1000, 1000)
        self.ax_2d.set_ylim(-1000, 1000)
        self.ax_2d.set_xlabel("t")
        self.ax_2d.set_ylabel("Velocity x")

        self.xlocs = df["true_state.state.x"].to_numpy()
        self.ylocs = df["true_state.state.y"].to_numpy()
        self.zlocs = df["true_state.state.z"].to_numpy()
        self.ts = df["true_state.time"].to_numpy()
        self.vel_xs = df["true_state.state.vel_x"].to_numpy()

        self.annot = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(20, 20),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"),
            arrowprops=dict(arrowstyle="->"),
        )
        self.annot.set_visible(False)
        self.sc = None

    def plot_data(self) -> None:
        """Procedure that plots a model of the earth, moon and the craft's trajectory in R3"""
        # 3D scatter plot of craft's trajectory
        self.sc = self.ax.scatter3D(self.xlocs, self.ylocs, self.zlocs, cmap="Greens")

        self.ax_2d.scatter(self.ts, self.vel_xs, cmap="Greens")

        # Calculation and plotting of earth's position
        u, v = np.mgrid[0 : 2 * np.pi : 20j, 0 : np.pi : 10j]
        earth_x = R_EARTH * np.cos(u) * np.sin(v)
        earth_y = R_EARTH * np.sin(u) * np.sin(v)
        earth_z = R_EARTH * np.cos(v)
        # self.ax.plot_surface(earth_x, earth_y, earth_z, color="g")

        # Calculation and plotting of moon's position
        moon_cx, moon_cy, moon_cz = get_body_position(self.ts[-1], BodyEnum.Moon)
        moon_x = moon_cx + R_MOON * np.cos(u) * np.sin(v)
        moon_y = moon_cy + R_MOON * np.sin(u) * np.sin(v)
        moon_z = moon_cz + R_MOON * np.cos(v)
        self.ax.plot_surface(moon_x, moon_y, moon_z, color="gray")

        # Calculation and plotting of sun's position
        # sun_cx, sun_cy, sun_cz = get_body_position(self.ts[-1], BodyEnum.Sun)
        # sun_x = sun_cx + R_SUN * np.cos(u) * np.sin(v)
        # sun_y = sun_cy + R_SUN * np.sin(u) * np.sin(v)
        # sun_z = sun_cz + R_SUN * np.cos(v)
        # self.ax.plot_surface(sun_x, sun_y, sun_z, color="y")

        self.fig.canvas.mpl_connect("motion_notify_event", self.hover)
        plt.show()

    def update_annot(self, ind):

        pos = self.sc.get_offsets()[ind["ind"][0]]
        self.annot.xy = pos
        # text = " ".join([str(self.ts[n]) for n in ind["ind"]])
        text = " ".join([str(self.ts[ind["ind"][0]])])

        self.annot.set_text(text)
        # self.annot.get_bbox_patch().set_facecolor(cmap(norm(c[ind["ind"][0]])))
        # self.annot.get_bbox_patch().set_alpha(0.4)

    def hover(self, event):
        vis = self.annot.get_visible()
        if event.inaxes == self.ax:
            cont, ind = self.sc.contains(event)
            if cont:
                self.update_annot(ind)
                self.annot.set_visible(True)
                self.fig.canvas.draw_idle()
            else:
                if vis:
                    self.annot.set_visible(False)
                    self.fig.canvas.draw_idle()
