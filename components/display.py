from components import bus

# Display driver for For Fun Virtual Computer
'''
VM Display Specifications:
    Resolution:
        320x200 pixels
    Depth:
        3 bits per pixel (indexed)
    Palette:
        8 * 1B (256 colour)
        Total = 8B

        000 000 00
        R   G   B
        
    Memory:
    0 to 23999:     colour
    24000 to 31999: text
    32000 to 32007: palette
    32008: text(0) or graphics(1) mode?
    32009: reserved
    
'''

# This display draws with pygame for simplicity, any library could be used
import pygame

pygame.init()


def display_msg(status_code, *args):
    status_messages = [
        "Negative write location",
        "Unknown display mode"
    ]
    if status_code >= len(status_messages):
        msg = "Unknown status code"
    else:
        msg = status_messages[status_code]

    print("Display message:", msg, *args)


class Screen:
    def __init__(self, host_width, host_height, true_width, true_height):

        # Simulated values
        self.resolution_on_host = (host_width, host_height)
        self.surface = pygame.display.set_mode(self.resolution_on_host)

        # Internal registers
        self.true_resolution = (true_width, true_height)
        self.palette = bytearray(8)
        self.mode = bytearray(1)

        # Useful magic numbers
        self.colour_bound = 24000
        self.text_bound = 32000
        self.palette_bound = 32008
        self.mode_bound = 32009

    def read(self, loc, size):
        return bus.io(2, loc, size)

    def write(self, loc, data):

        if type(data) == int:
            data = data.to_bytes(2, "little")

        if loc < 0:
            display_msg(0)
            quit()

        # The first 24kB are graphical data
        graphics = data[loc:self.colour_bound]

        # The next 8kB are text data
        text = data[self.colour_bound - loc:self.text_bound]

        # The palette is stored in the next 8 bytes
        palette = data[self.text_bound - loc:self.palette_bound - loc]

        # What mode are we in?
        mode = data[self.palette_bound - loc:self.mode_bound - loc]

        # The final byte is reserved
        reserved = data[self.mode_bound - loc:32010]

        # If palette data was given, store it in the palette register
        if len(palette) > 0:
            self.palette[:len(palette)] = palette

        # If a mode was given, store it in the mode register
        if len(mode) > 0:
            self.mode[:len(mode)] = mode

        # Graphics mode
        if self.mode[0] == 0:
            # Set up a bitstring for the graphics data
            bit_graphics = ""
            # Reformat the graphics data into bits
            for g in graphics:
                bitstring = format(g, 'b')
                prefix = '0' * (8 - len(bitstring))
                bitstring = prefix + bitstring
                bit_graphics += bitstring

            # Convert 3-bit strings into useable ints
            bit_graphics = [bit_graphics[i:i + 3] for i in range(0, len(bit_graphics), 3)]
            bit_graphics = [int(v, 2) for v in bit_graphics]

            pixel_width = self.resolution_on_host[0] / self.true_resolution[0]
            pixel_height = self.resolution_on_host[1] / self.true_resolution[1]

            # Iterate over the graphics data and draw every pixel...
            x_draw = 0
            y_draw = 0

            for g in bit_graphics:
                c = self.palette[g]
                c_bits = format(c, 'b')
                prefix = '0' * (8 - len(c_bits))
                c_bits = prefix + c_bits

                r = int(c_bits[:3], 2)
                g = int(c_bits[3:6], 2)
                b = int(c_bits[6:8], 2)

                # Convert r, g, and b into modern 24-bit rgb equivalents
                r *= 32
                g *= 32
                b *= 64

                pygame.draw.rect(self.surface, (r, g, b),
                                 (x_draw * pixel_width, y_draw * pixel_height, pixel_width, pixel_height))

                if x_draw >= self.true_resolution[0] - 1:
                    x_draw = 0
                    y_draw += 1
                else:
                    x_draw += 1

        # Text mode
        elif self.mode[0] == 1:
            y = 0
            font_location_offset = 500

            font_header = bus.io(2, bus.reserved_bytes + font_location_offset, 4)
            font_size = font_header[3]
            font = bus.io(2, bus.reserved_bytes + font_location_offset, 4 + 9 * font_size)
            font_keys = [font[i + 4] for i in range(0, len(font) - 4, 9)]
            font_glyphs = [font[i + 1: i + 9] for i in range(4, len(font) - 1, 9)]

            # Assemble the key-glyph font mapping
            fontmap = {}
            for i in range(len(font_keys)):
                k = font_keys[i]
                fontmap[k] = font_glyphs[i]

            # Ensure the fontmap always contains a null glyph for fallback
            fontmap[0x00] = bytes(8)

            text_data = bus.io(2, 1000 + self.colour_bound, 4000)

            glyph_surface = pygame.Surface((8, 8))
            chars_per_line = self.true_resolution[0] // 8
            chars_per_column = self.true_resolution[1] // 8

            x = 0
            # Iterate over each character ID
            for c in text_data:
                # Catch control characters
                # Null
                if c == 0x00:
                    continue

                # Newline
                elif c == 0x05:
                    bus.io(1, 22, y + 1)
                    continue

                # Home
                elif c == 0x0e:
                    bus.io(1, 22, 0)
                    continue

                gx = 0
                gy = 0
                y = bus.io(0, 22, 1)

                # Make sure the loaded font supports the current character
                try:
                    glyph = fontmap[c]

                # Fall back to the 0x00 char if char is unsupported
                except KeyError:
                    glyph = fontmap[0x00]

                # Convert glyph data into an array of bits
                glyph_bitstring_rows = []
                for glyph_row in glyph:
                    row_bitstring = format(glyph_row, 'b')
                    prefix = '0' * (8 - len(row_bitstring))
                    row_bitstring = prefix + row_bitstring
                    glyph_bitstring_rows.append(row_bitstring)

                # Render each array of bits onto a pygame surface
                for glyph_bs_row in glyph_bitstring_rows:
                    for bit in glyph_bs_row:
                        c = self.palette[int(bit)]
                        c_bits = format(c, 'b')
                        prefix = '0' * (8 - len(c_bits))
                        c_bits = prefix + c_bits

                        r = int(c_bits[:3], 2)
                        g = int(c_bits[3:6], 2)
                        b = int(c_bits[6:8], 2)

                        # Convert r, g, and b into modern 24-bit rgb equivalents
                        r *= 32
                        g *= 32
                        b *= 64

                        # Render a single pixel by drawing a line from one point to the same point
                        pygame.draw.line(glyph_surface, (r, g, b), (gx, gy), (gx, gy))
                        gx += 1

                    gy += 1
                    gx = 0

                self.surface.blit(glyph_surface, (8 * x, 8 * y))
                x += 1

                # If we have reached the end of the line...
                if x >= chars_per_line:
                    # Increment the line register and reset the x pos
                    bus.io(1, 22, y + 1)
                    x = 0

                # Wrap the line register if we try to draw text beyond the bottom of the screen
                if y >= chars_per_column and False:
                    print("Wrapping y:", y, '/', chars_per_column)
                    bus.io(1, 22, 0)

        else:
            display_msg(1, self.mode)
            quit()

        pygame.display.flip()
