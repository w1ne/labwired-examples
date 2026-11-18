//
// A read-only VFS that exposes the memory-mapped IWAD as /doom/doom1.wad.
//
// doomgeneric checks the IWAD with fopen() before it ever calls W_OpenFile
// (D_FindWADByName -> M_FileExists). Without a filesystem behind that name
// D_DoomMain aborts with "IWAD file not found" even though the WAD is sitting
// in flash. This gives that path something real to stat and read, while the
// bulk lump access still goes through the mapped pointer in w_file_flash.c.
//

#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/unistd.h>

#include "esp_log.h"
#include "esp_vfs.h"

#include "doom_esp32.h"

#define DOOM_VFS_MOUNT "/doom"
#define DOOM_VFS_NAME "/doom1.wad"
#define DOOM_VFS_MAX_FDS 4

static const char *TAG = "doom_vfs";

typedef struct
{
    bool in_use;
    off_t pos;
} doom_vfs_fd_t;

static doom_vfs_fd_t s_fds[DOOM_VFS_MAX_FDS];

static int doom_vfs_open(const char *path, int flags, int mode)
{
    int i;

    (void)mode;

    if (path == NULL || strcmp(path, DOOM_VFS_NAME) != 0)
    {
        errno = ENOENT;
        return -1;
    }

    // Read-only: the WAD is in flash behind the instruction/data cache.
    if ((flags & O_ACCMODE) != O_RDONLY)
    {
        errno = EROFS;
        return -1;
    }

    if (doom_wad_base == NULL)
    {
        errno = ENOENT;
        return -1;
    }

    for (i = 0; i < DOOM_VFS_MAX_FDS; ++i)
    {
        if (!s_fds[i].in_use)
        {
            s_fds[i].in_use = true;
            s_fds[i].pos = 0;
            return i;
        }
    }

    errno = EMFILE;
    return -1;
}

static ssize_t doom_vfs_read(int fd, void *dst, size_t size)
{
    size_t available;

    if (fd < 0 || fd >= DOOM_VFS_MAX_FDS || !s_fds[fd].in_use)
    {
        errno = EBADF;
        return -1;
    }

    if ((size_t)s_fds[fd].pos >= doom_wad_length)
    {
        return 0;
    }

    available = doom_wad_length - (size_t)s_fds[fd].pos;

    if (size > available)
    {
        size = available;
    }

    memcpy(dst, doom_wad_base + s_fds[fd].pos, size);
    s_fds[fd].pos += size;

    return (ssize_t)size;
}

static off_t doom_vfs_lseek(int fd, off_t offset, int mode)
{
    off_t next;

    if (fd < 0 || fd >= DOOM_VFS_MAX_FDS || !s_fds[fd].in_use)
    {
        errno = EBADF;
        return -1;
    }

    switch (mode)
    {
        case SEEK_SET: next = offset; break;
        case SEEK_CUR: next = s_fds[fd].pos + offset; break;
        case SEEK_END: next = (off_t)doom_wad_length + offset; break;
        default:
            errno = EINVAL;
            return -1;
    }

    if (next < 0)
    {
        errno = EINVAL;
        return -1;
    }

    s_fds[fd].pos = next;
    return next;
}

static int doom_vfs_close(int fd)
{
    if (fd < 0 || fd >= DOOM_VFS_MAX_FDS || !s_fds[fd].in_use)
    {
        errno = EBADF;
        return -1;
    }

    s_fds[fd].in_use = false;
    return 0;
}

static void doom_vfs_fill_stat(struct stat *st)
{
    memset(st, 0, sizeof(*st));
    st->st_mode = S_IFREG | 0444;
    st->st_size = (off_t)doom_wad_length;
}

static int doom_vfs_fstat(int fd, struct stat *st)
{
    if (fd < 0 || fd >= DOOM_VFS_MAX_FDS || !s_fds[fd].in_use)
    {
        errno = EBADF;
        return -1;
    }

    doom_vfs_fill_stat(st);
    return 0;
}

static int doom_vfs_stat(const char *path, struct stat *st)
{
    if (path == NULL || strcmp(path, DOOM_VFS_NAME) != 0 || doom_wad_base == NULL)
    {
        errno = ENOENT;
        return -1;
    }

    doom_vfs_fill_stat(st);
    return 0;
}

esp_err_t doom_vfs_register(void)
{
    esp_vfs_t vfs = {
        .flags = ESP_VFS_FLAG_DEFAULT,
        .open = &doom_vfs_open,
        .close = &doom_vfs_close,
        .read = &doom_vfs_read,
        .lseek = &doom_vfs_lseek,
        .fstat = &doom_vfs_fstat,
        .stat = &doom_vfs_stat,
    };

    esp_err_t err = esp_vfs_register(DOOM_VFS_MOUNT, &vfs, NULL);

    if (err != ESP_OK)
    {
        ESP_LOGE(TAG, "esp_vfs_register(%s) failed: %s", DOOM_VFS_MOUNT,
                 esp_err_to_name(err));
    }

    return err;
}

const char *doom_vfs_iwad_path(void)
{
    return DOOM_VFS_MOUNT DOOM_VFS_NAME;
}
