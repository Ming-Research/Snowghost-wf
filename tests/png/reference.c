/*
 * The PNG oracle's reference: decodes with libpng to the RGBA form that
 * pkg::image::png promises, generates the speed set, and times libpng on it.
 *
 *   reference decode IN.png OUT.rgba   exit 1 when libpng rejects IN
 *   reference generate DIR             write the twelve speed-set images
 *   reference time REPEAT FILE...      decode every FILE REPEAT times
 *
 * OUT.rgba holds the width and height as little-endian u32, then the pixels.
 */
#include <png.h>
#include <setjmp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct image {
    uint32_t width, height;
    unsigned char *pixels;
};

struct source {
    const unsigned char *data;
    size_t size, at;
};

static void read_source(png_structp png, png_bytep out, size_t count) {
    struct source *source = png_get_io_ptr(png);
    if (source->size - source->at < count)
        png_error(png, "unexpected end of data");
    memcpy(out, source->data + source->at, count);
    source->at += count;
}

static void quiet(png_structp png, png_const_charp message) {
    (void)png;
    (void)message;
}

static void fail(png_structp png, png_const_charp message) {
    (void)message;
    png_longjmp(png, 1);
}

/* The transforms match the interface: expand palette, low-depth gray and
 * tRNS; keep the high byte of 16-bit samples; gray to RGB; opaque filler.
 * No gamma transform is requested, so gAMA and the like are ignored. */
static int decode(const unsigned char *data, size_t size, struct image *out) {
    png_structp png = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, fail, quiet);
    png_infop info = png ? png_create_info_struct(png) : NULL;
    unsigned char *volatile pixels = NULL;
    png_bytep *volatile rows = NULL;
    if (!info) {
        png_destroy_read_struct(&png, NULL, NULL);
        return 0;
    }
    if (setjmp(png_jmpbuf(png))) {
        free(pixels);
        free(rows);
        png_destroy_read_struct(&png, &info, NULL);
        return 0;
    }
    struct source source = {data, size, 0};
    png_set_read_fn(png, &source, read_source);
    png_read_info(png, info);
    png_uint_32 width = png_get_image_width(png, info);
    png_uint_32 height = png_get_image_height(png, info);
    int color = png_get_color_type(png, info);
    png_set_expand(png);
    png_set_strip_16(png);
    if (color == PNG_COLOR_TYPE_GRAY || color == PNG_COLOR_TYPE_GRAY_ALPHA)
        png_set_gray_to_rgb(png);
    png_set_filler(png, 0xff, PNG_FILLER_AFTER);
    png_set_interlace_handling(png);
    png_read_update_info(png, info);
    if (png_get_rowbytes(png, info) != (size_t)width * 4)
        png_error(png, "unexpected row size");
    pixels = malloc((size_t)width * height * 4);
    rows = malloc(sizeof(png_bytep) * height);
    if (!pixels || !rows)
        png_error(png, "out of memory");
    for (png_uint_32 y = 0; y < height; y++)
        rows[y] = pixels + (size_t)y * width * 4;
    png_read_image(png, rows);
    png_read_end(png, NULL);
    free(rows);
    png_destroy_read_struct(&png, &info, NULL);
    out->width = width;
    out->height = height;
    out->pixels = pixels;
    return 1;
}

static unsigned char *read_file(const char *path, size_t *size) {
    FILE *file = fopen(path, "rb");
    if (!file) {
        perror(path);
        exit(2);
    }
    fseek(file, 0, SEEK_END);
    long length = ftell(file);
    fseek(file, 0, SEEK_SET);
    unsigned char *data = malloc(length > 0 ? length : 1);
    if (!data || fread(data, 1, length, file) != (size_t)length) {
        perror(path);
        exit(2);
    }
    fclose(file);
    *size = length;
    return data;
}

static void put_u32(FILE *file, uint32_t value) {
    unsigned char bytes[4] = {value, value >> 8, value >> 16, value >> 24};
    fwrite(bytes, 1, 4, file);
}

static int decode_command(const char *in, const char *out) {
    size_t size;
    unsigned char *data = read_file(in, &size);
    struct image image;
    if (!decode(data, size, &image))
        return 1;
    FILE *file = fopen(out, "wb");
    if (!file) {
        perror(out);
        return 2;
    }
    put_u32(file, image.width);
    put_u32(file, image.height);
    fwrite(image.pixels, 1, (size_t)image.width * image.height * 4, file);
    return fclose(file) ? 2 : 0;
}

static int time_command(int repeat, int count, char **paths) {
    uint64_t checksum = 0;
    for (int i = 0; i < count; i++) {
        size_t size;
        unsigned char *data = read_file(paths[i], &size);
        for (int r = 0; r < repeat; r++) {
            struct image image;
            if (!decode(data, size, &image)) {
                fprintf(stderr, "%s: rejected\n", paths[i]);
                return 1;
            }
            size_t length = (size_t)image.width * image.height * 4;
            for (size_t at = 0; at < length; at += 4093)
                checksum += image.pixels[at];
            free(image.pixels);
        }
        free(data);
    }
    printf("checksum %llu\n", (unsigned long long)checksum);
    return 0;
}

/* The speed set: deterministic 2048 by 2048 content, encoded by libpng with
 * its default compression and filter settings. */
enum { SIDE = 2048 };

static uint32_t state = 12345;

static uint32_t next_random(void) {
    state = state * 1103515245u + 12345u;
    return state >> 8;
}

static int glyph_ink(uint32_t x, uint32_t y) {
    /* Synthetic text: 8 by 12 cells holding pseudo-glyphs in lines. */
    uint32_t line = y / 16, row = y % 16, cell = x / 8, column = x % 8;
    if (row >= 12 || column >= 6 || (cell + line * 7) % 11 == 0)
        return 0;
    uint32_t seed = (cell * 2654435761u) ^ (line * 40503u);
    uint32_t bits = seed ^ (seed >> 13) ^ (row * 0x9e3779b9u);
    return (bits >> column) & 1;
}

static void pixel(int kind, uint32_t x, uint32_t y, unsigned char *out) {
    uint32_t noise = next_random();
    switch (kind) {
    case 0: /* RGB gradient */
    case 9: /* the same, interlaced */
        out[0] = x * 255 / (SIDE - 1);
        out[1] = y * 255 / (SIDE - 1);
        out[2] = (x + y) * 255 / (2 * SIDE - 2);
        out[3] = 255;
        break;
    case 1: /* RGBA gradient with an alpha ramp */
        out[0] = y * 255 / (SIDE - 1);
        out[1] = 128;
        out[2] = x * 255 / (SIDE - 1);
        out[3] = (x ^ y) & 255;
        break;
    case 2: /* RGB noise */
        out[0] = noise;
        out[1] = noise >> 8;
        out[2] = noise >> 16;
        out[3] = 255;
        break;
    case 3: /* gray noise */
    case 10: /* gray and alpha noise */
        out[0] = out[1] = out[2] = noise;
        out[3] = kind == 10 ? noise >> 8 : 255;
        break;
    case 4: /* black text on white, RGB */
    case 5: /* the same, gray */
        out[0] = out[1] = out[2] = glyph_ink(x, y) ? 0 : 255;
        out[3] = 255;
        break;
    case 6: { /* 256-color blocks, palette */
        uint32_t index = ((x / 32) * 7 + (y / 32) * 13) & 255;
        out[0] = index;
        out[1] = index * 3;
        out[2] = index * 7;
        out[3] = 255;
        break;
    }
    case 7: { /* a user interface: panels, bars and text */
        int panel = (x / 256 + y / 192) % 3;
        unsigned char base[3][3] = {{245, 245, 247}, {32, 33, 36}, {66, 133, 244}};
        memcpy(out, base[panel], 3);
        if (y % 192 < 24)
            out[0] = out[1] = out[2] = 220 - (y % 192) * 2;
        if (glyph_ink(x, y))
            out[0] = out[1] = out[2] = panel == 1 ? 230 : 20;
        out[3] = x % 256 < 4 ? 128 : 255;
        break;
    }
    case 11: { /* smooth value noise, like a photograph */
        uint32_t cx = x / 64, cy = y / 64;
        uint32_t h = (cx * 73856093u) ^ (cy * 19349663u);
        out[0] = (h & 255) * 3 / 4 + (x & 63);
        out[1] = ((h >> 8) & 255) * 3 / 4 + (y & 63);
        out[2] = ((h >> 16) & 255) * 3 / 4 + (noise & 15);
        out[3] = 255;
        break;
    }
    default: /* case 8: 16-bit RGB gradient, high bytes here */
        out[0] = x >> 3;
        out[1] = y >> 3;
        out[2] = (x * y) >> 14;
        out[3] = 255;
        break;
    }
}

static int write_image(const char *dir, int kind) {
    static const struct {
        const char *name;
        int color, depth, interlace;
    } kinds[12] = {
        {"rgb-gradient", PNG_COLOR_TYPE_RGB, 8, 0},
        {"rgba-gradient", PNG_COLOR_TYPE_RGB_ALPHA, 8, 0},
        {"rgb-noise", PNG_COLOR_TYPE_RGB, 8, 0},
        {"gray-noise", PNG_COLOR_TYPE_GRAY, 8, 0},
        {"rgb-text", PNG_COLOR_TYPE_RGB, 8, 0},
        {"gray-text", PNG_COLOR_TYPE_GRAY, 8, 0},
        {"palette-blocks", PNG_COLOR_TYPE_PALETTE, 8, 0},
        {"rgba-interface", PNG_COLOR_TYPE_RGB_ALPHA, 8, 0},
        {"rgb16-gradient", PNG_COLOR_TYPE_RGB, 16, 0},
        {"rgb-gradient-adam7", PNG_COLOR_TYPE_RGB, 8, 1},
        {"gray-alpha-noise", PNG_COLOR_TYPE_GRAY_ALPHA, 8, 0},
        {"rgb-photo", PNG_COLOR_TYPE_RGB, 8, 0},
    };
    char path[4096];
    snprintf(path, sizeof path, "%s/%02d-%s.png", dir, kind, kinds[kind].name);
    FILE *file = fopen(path, "wb");
    if (!file) {
        perror(path);
        return 2;
    }
    png_structp png = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    png_infop info = png_create_info_struct(png);
    if (setjmp(png_jmpbuf(png)))
        return 2;
    png_init_io(png, file);
    int color = kinds[kind].color, depth = kinds[kind].depth;
    png_set_IHDR(png, info, SIDE, SIDE, depth, color,
                 kinds[kind].interlace ? PNG_INTERLACE_ADAM7 : PNG_INTERLACE_NONE,
                 PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
    if (color == PNG_COLOR_TYPE_PALETTE) {
        png_color palette[256];
        for (int i = 0; i < 256; i++) {
            palette[i].red = i;
            palette[i].green = i * 3;
            palette[i].blue = i * 7;
        }
        png_set_PLTE(png, info, palette, 256);
    }
    png_write_info(png, info);
    int channels = color == PNG_COLOR_TYPE_RGB ? 3
                 : color == PNG_COLOR_TYPE_RGB_ALPHA ? 4
                 : color == PNG_COLOR_TYPE_GRAY_ALPHA ? 2 : 1;
    size_t row_bytes = (size_t)SIDE * channels * (depth / 8);
    unsigned char *image = malloc(row_bytes * SIDE);
    for (uint32_t y = 0; y < SIDE; y++) {
        unsigned char *row = image + y * row_bytes;
        for (uint32_t x = 0; x < SIDE; x++) {
            unsigned char rgba[4];
            pixel(kind, x, y, rgba);
            if (color == PNG_COLOR_TYPE_PALETTE) {
                row[x] = rgba[0];
            } else if (depth == 16) {
                for (int c = 0; c < 3; c++) {
                    row[x * 6 + c * 2] = rgba[c];
                    row[x * 6 + c * 2 + 1] = (x + y + c) & 255;
                }
            } else if (channels == 1 || channels == 2) {
                row[x * channels] = rgba[0];
                if (channels == 2)
                    row[x * 2 + 1] = rgba[3];
            } else {
                memcpy(row + x * channels, rgba, channels);
            }
        }
    }
    png_bytep *rows = malloc(sizeof(png_bytep) * SIDE);
    for (uint32_t y = 0; y < SIDE; y++)
        rows[y] = image + y * row_bytes;
    png_write_image(png, rows);
    png_write_end(png, NULL);
    png_destroy_write_struct(&png, &info);
    free(rows);
    free(image);
    return fclose(file) ? 2 : 0;
}

int main(int argc, char **argv) {
    if (argc == 4 && strcmp(argv[1], "decode") == 0)
        return decode_command(argv[2], argv[3]);
    if (argc == 3 && strcmp(argv[1], "generate") == 0) {
        for (int kind = 0; kind < 12; kind++)
            if (write_image(argv[2], kind))
                return 2;
        return 0;
    }
    if (argc >= 4 && strcmp(argv[1], "time") == 0)
        return time_command(atoi(argv[2]), argc - 3, argv + 3);
    fprintf(stderr, "usage: reference decode IN.png OUT.rgba | generate DIR | time REPEAT FILE...\n");
    return 2;
}
