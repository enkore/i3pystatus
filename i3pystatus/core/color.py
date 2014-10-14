from colour import Color


class ColorRangeModule(object):
    """
    Class to dynamically generate and select colors.

    Requires the PyPI package `colour`
    """

    start_color = "#00FF00"
    end_color = 'red'

    @staticmethod
    def get_hex_color_range(start_color, end_color, quantity):
        """
        Generates a list of quantity Hex colors from start_color to end_color.

        :param start_color: Hex or plain English color for start of range
        :param end_color: Hex or plain English color for end of range
        :param quantity: Number of colours to return
        :return: A list of Hex color values
        """
        raw_colors = [c.hex for c in list(Color(start_color).range_to(Color(end_color), quantity))]
        colors = []
        for color in raw_colors:

            # i3bar expects the full Hex value but for some colors the colour
            # module only returns partial values. So we need to convert these colors to the full
            # Hex value.
            if len(color) == 4:
                fixed_color = "#"
                for c in color[1:]:
                    fixed_color += c * 2
                colors.append(fixed_color)
            else:
                colors.append(color)
        return colors

    def get_gradient(self, value, colors, upper_limit=100):
        """
        Map a value to a color
        :param value: Some value
        :return: A Hex color code
        """
        index = int(self.percentage(value, upper_limit))
        if index >= len(colors):
            return colors[-1]
        elif index < 0:
            return colors[0]
        else:
            return colors[index]

    @staticmethod
    def percentage(part, whole):
        """
        Calculate percentage
        """
        if whole == 0:
            return 0
        return 100 * float(part) / float(whole)
