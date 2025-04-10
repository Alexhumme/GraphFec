# importaciones
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as pts
from matplotlib.lines import Line2D
import numpy as np

matplotlib.use("svg")

import flet as ft
from flet.matplotlib_chart import MatplotlibChart

from utils.get_phase import main as get_phase
from utils.phases_data import data as phases
import utils.styles as styles

# Componentes que pertenecen a la interface de la aplicacion
# gui
appbar = ft.AppBar(
    **styles.interface.get("appbar"),
    title=ft.Text("FecGraph"),
    actions=[
        ft.IconButton(ft.icons.DARK_MODE_OUTLINED, tooltip="modo"),
        ft.PopupMenuButton(
            tooltip="Opciones",
            items=[ft.PopupMenuItem(icon=ft.icons.DOWNLOAD, text="Descargar Manual")],
        ),
    ],
)


class Sidebar(ft.Container):
    def __init__(self):
        super().__init__(**styles.interface.get("sidebar"))

        self.phase_card = Compoundcard()

        self.temperature = InfoCard(val_info=20, val_suf="°F", var_name="T°")
        self.percentage = InfoCard(val_suf="%", var_name="C%")

        self.t_input = ft.Slider(**styles.interface.get("field_t"), label="{value}°F")
        self.p_input = ft.Slider(**styles.interface.get("field_p"), label="{value}%")

        self.chartSwitcher = chartSwitcher()

        self.content = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.VerticalAlignment.CENTER,
            controls=[
                self.phase_card,
                self.temperature,
                self.t_input,
                self.percentage,
                self.p_input,
                # self.chartSwitcher,
            ],
        )
    def updateInfo(self, data, index):
        img_name = data[index].get('img')
        self.phase_card.updateImage(f"/images/{img_name}")
        pass

class Compoundcard(ft.Image):  # tarjeta superior de la barra derecha, muestra la estructura crristalina del compuesto
    def __init__(self):
        super().__init__(
            height=170,
            width=170,
            repeat=ft.ImageRepeat.NO_REPEAT,
            border_radius=ft.border_radius.all(10),
            src='./eve.png'
        )
        pass

    def updateImage(self, route):
        self.src = route
        self.update()
        pass

class InfoCard(ft.Container):  # musetra informacion de una variable en la barra lateral
    def __init__(self, val_info=0, val_suf="", var_name=""):
        super().__init__(**styles.interface.get("card_main"))

        self.var_name = var_name
        self.val_suf = val_suf
        self.val_info = val_info

        self.var_text = ft.Text(  # variable en la esquina izquiera
            self.var_name,
            color=ft.colors.SURFACE_TINT,
            weight=ft.FontWeight.W_900,
        )
        self.val_text = ft.Text(  # valor actual en el centro
            f"{self.val_info}{self.val_suf}",
            color=ft.colors.SURFACE_TINT,
            weight=ft.FontWeight.W_700,
            size=45,
        )

        self.content = ft.Column(
            controls=[
                ft.Container(height=20, content=self.var_text),
                ft.Container(
                    bgcolor=ft.colors.SECONDARY_CONTAINER,
                    border_radius=ft.BorderRadius(10, 10, 10, 10),
                    alignment=ft.alignment.center,
                    content=self.val_text,
                ),
            ]
        )

    def updateValue(self, new_value):  # actualizar valor, recibe un valor y lo añade
        self.val_info = new_value
        self.val_text.value = f"{self.val_info}{self.val_suf}"
        self.val_text.update()


class InfoSnack(
    ft.Container
):  # barras al derecho del grafico, muestran informacion de la seleccion actual
    def __init__(self, var="None", value="--"):
        super().__init__(**styles.interface.get("infosnack"))
        self.content = ft.Row(
            controls=[
                ft.Container(
                    padding=ft.Padding(20, 10, 0, 10),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    expand=True,
                    content=ft.Text(var, weight=ft.FontWeight.W_600),
                ),
                ft.Container(
                    padding=ft.Padding(0, 10, 0, 10),
                    alignment=ft.alignment.center,
                    bgcolor=ft.colors.SECONDARY_CONTAINER,
                    expand=True,
                    content=ft.Text(value, color=ft.colors.SURFACE_TINT),
                ),
            ]
        )


class PhaseLine(ft.LineChartData):
    def __init__(self, phaseData: dict):
        super().__init__()
        self.stroke_width = (2,)
        self.curved = (True, True)
        self.phase_data = phaseData
        self.color = self.phase_data["line_properties"]["color"]
        self.data_points = self.convert_to_chart_data(self.phase_data["line"])

    def convert_to_chart_data(
        self, line_data: list[tuple[float, float]]
    ) -> list[ft.LineChartDataPoint]:
        chart_data_points = []
        for point in line_data:
            x, y = point
            data_point = ft.LineChartDataPoint(
                x=x, y=y, show_tooltip=True, tooltip=self.phase_data["name"]
            )
            chart_data_points.append(data_point)
        return chart_data_points


# chart
class FecMatPlotChart(MatplotlibChart):
    def __init__(self):
        super().__init__()
        fig, self.ax = plt.subplots()  # axes and figure
        self.figure = fig
        self.cursor = None  # Almacenamiento para el cursor
        self.cross_lines = []  # Almacenamiento para las líneas de la cruz
        self.filled_area = None

        # appearance
        self.border = ft.Border(
            ft.BorderSide(2, ft.colors.SURFACE),
            ft.BorderSide(2, ft.colors.SURFACE),
            ft.BorderSide(2, ft.colors.SURFACE),
            ft.BorderSide(2, ft.colors.SURFACE),
        )
        self.border_radius = ft.BorderRadius(10, 10, 10, 10)

        # testing
        self.test_index = 0

        self.drawBase()
        self.drawChart()

    def drawBase(self):
        self.ax.set_ylabel("Temperatura (°F)")
        self.ax.set_xlabel("Porcentaje de carbono (C%)")
        self.ax.set_xlim(0, 7)
        self.ax.set_ylim(20, 1600)
        self.ax.grid()

    def drawChart(self):
        phase_lines: list = [
            self.ax.plot(
                phase_data["line_x"],
                phase_data["line_y"],
                phase_data["line_properties"]["color"],
            )
            for phase_data in phases
            if phase_data.get("line_properties")
        ]

    def drawFill(self, data):
        if self.filled_area:
            for patch in self.filled_area: patch.remove()
            self.filled_area = None

        phase_name = data[0].get('name')
        matching_phase = next((phase for phase in phases if phase.get('name') == phase_name), None)

        if matching_phase:
            self.filled_area = self.ax.fill(matching_phase["line_x"], matching_phase["line_y"], alpha=0.5, color='blue')

    def drawCursor(self, x, y):
        # Eliminar el cursor anterior si existe
        if self.cursor:
            for line in self.cross_lines: line.remove()
            self.cross_lines = []
            self.cursor.remove()
            self.cursor = None

        # Calculate the aspect ratio
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        aspect_ratio = (xlim[1] - xlim[0]) / (ylim[1] - ylim[0])

        # Define the radius
        radius_x = 0.5  # Horizontal radius
        radius_y = 1.3 * radius_x / aspect_ratio  # Vertical radius

        # Calcular los vértices del polígono simétrico (en este caso, un polígono de 20 lados)
        num_vertices = 20
        angles = np.linspace(0, 2 * np.pi, num_vertices)
        vertices = np.vstack((x + radius_x * np.cos(angles), y + radius_y * np.sin(angles))).T

        # Dibujar el polígono con relleno semitransparente
        self.cursor = pts.Polygon(vertices, closed=True, edgecolor='r', facecolor='r', alpha=0.5)
        self.ax.add_patch(self.cursor)

        # Draw a small cross in the center of the ellipse
        cross_sizeX = 0.1  # Size x of the cross
        cross_sizeY = 1.3 * cross_sizeX / aspect_ratio  # Size y of the cross

        # Draw horizontal line of the cross
        horizontal_line = Line2D([x - cross_sizeX, x + cross_sizeX], [y, y], color='black', lw=1)
        self.ax.add_line(horizontal_line)
        self.cross_lines.append(horizontal_line)

        # Draw vertical line of the cross
        vertical_line = Line2D([x, x], [y - cross_sizeY, y + cross_sizeY], color='black', lw=1)
        self.ax.add_line(vertical_line)
        self.cross_lines.append(vertical_line)

    def updateChart(self, pos, data):
        if data : self.drawFill(data)
        self.drawCursor(pos[0], pos[1]) # mover cursor
        self.update()

# view
class ViewUpperpart(ft.Tabs):
    def __init__(self):
        super().__init__(height=200)

        self.container = ft.Container(**styles.interface.get("panel"))
        self.tabs = [ft.Tab(content=self.container)]

    def updateInfo(self, data):
        self.data = data
        self.tabs = self._build_tabs()
        self.update()

    def _build_tabs(self):
        return [
            ft.Tab(
                text=self._format_tab_text(item),
                content=ft.Container(
                    **styles.interface.get("panel"),
                    content=ft.Text(
                        self._get_phase_description(item["name"]),
                        color=ft.colors.SURFACE,
                    ),
                ),
            )
            for item in self.data
        ]

    def _format_tab_text(self, item):
        pure_text = "pura" if item.get("pure") else ""
        num_text = str(item.get("num") or "")
        porc_text = "%.1f" % (item.get("porc") or 0)
        return f"{item['name']} {pure_text} {num_text} ({porc_text})%"

    def _get_phase_description(self, phase_name):
        return next(
            filter(lambda phase: phase.get("name") == phase_name, self.phases), {}
        ).get("description")

class ViewLowerpart(ft.Container):
    def __init__(self):
        super().__init__(expand=True)
        self.chart = FecMatPlotChart()
        self.props_list_view = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True
        )
        self.content = ft.Row(
            controls=[
                ft.Container(
                    **styles.interface.get("card_tight"),
                    expand=True,
                    content=self.chart,
                ),
                ft.Container(
                    **styles.interface.get("card_main"),
                    width=220,
                    content=self.props_list_view,
                ),
            ]
        )

    def updateProperties(self, data):
        info_snacks = (
            [InfoSnack(prop.get("name"), prop.get("val")) for prop in data]
            if data
            else []
        )
        self.props_list_view.controls.clear()
        self.props_list_view.controls.extend(info_snacks)
        self.props_list_view.update()

    def setChart(self, chart):
        self.content = ft.Row(
            controls=[
                ft.Container(
                    expand=True, padding=ft.Padding(10, 10, 10, 10), content=chart
                ),
                ft.Container(
                    **styles.interface.get("card_main"),
                    width=220,
                    content=self.props_list_view,
                ),
            ]
        )
        self.update()


class View(ft.Container):
    def __init__(self):
        super().__init__(**styles.interface.get("view"))
        self.upperpart: ViewUpperpart = ViewUpperpart()
        self.lowerpart: ViewLowerpart = ViewLowerpart()
        self.content = ft.Column(controls=[self.upperpart, self.lowerpart])

    pass


class FecGraph(ft.Container):
    def __init__(self, view: View, sidebar: Sidebar):
        self.current_data = None
        self.phases = phases

        self.t_counter = 0
        self.p_counter = 0

        self.view: View = view
        self.sidebar: Sidebar = sidebar

        self.sidebar.t_input.on_change = lambda e: self.view.lowerpart.chart.updateChart((self.sidebar.p_input.value, e.control.value), self.current_data)
        self.sidebar.p_input.on_change = lambda e: self.view.lowerpart.chart.updateChart((e.control.value, self.sidebar.t_input.value), self.current_data)
        self.sidebar.t_input.on_change_end = lambda e: self.update_values(e)
        self.sidebar.p_input.on_change_end = lambda e: self.update_values(e)

        self.sidebar.chartSwitcher.on_change = lambda e: self.switchChart(str(e.data))

        self.view.lowerpart.phases = self.phases
        self.view.upperpart.phases = self.phases
        self.sidebar.phases = self.phases
        self.view.phases = self.phases

        self.view.upperpart.on_change = lambda e: self.update_properties(int(e.data))

        super().__init__(
            **styles.interface.get("main"),
            content=ft.Row(controls=[self.view, self.sidebar], expand=True),
        )

    def update_values(self, event):

        t_delta: str = self.sidebar.t_input.value
        p_delta: str = self.sidebar.p_input.value

        self.t_counter = t_delta
        self.sidebar.temperature.updateValue("%.0f" % self.t_counter)

        self.p_counter = p_delta
        self.sidebar.percentage.updateValue(self.p_counter)

        self.current_data = get_phase(p_delta, t_delta) or [{"name": "None"}]
        self.sidebar.updateInfo(self.current_data, 0)
        self.view.upperpart.updateInfo(self.current_data)
        self.update_properties()
        self.update_chart()

    def update_properties(self, index=0):

        properties: list = next(
            filter(
                lambda phase: phase.get("name") == self.current_data[index].get("name"),
                self.phases,
            ),
            {},
        ).get("properties")
        self.view.lowerpart.updateProperties(properties)

    def update_chart(self):
        pass


class chartSwitcher(ft.SegmentedButton):
    def __init__(self):
        super().__init__(
            [
                ft.Segment("1", label=ft.Text("f")),
                ft.Segment("2", label=ft.Text("p")),
                ft.Segment("3", label=ft.Text("m")),
            ],
            selected=[1],
        )


# main
def main(page: ft.Page):
    page.title = "FecGraph"
    page.appbar = appbar

    view: ft.Container = View()
    sidebar: ft.Container = Sidebar()
    app: ft.Container = FecGraph(view=view, sidebar=sidebar)

    page.add(app)


ft.app(target=main, assets_dir="./resources")
