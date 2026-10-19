#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>
#include <wchar.h>

static unsigned long frame_number;
static const wchar_t window_class[] = L"NexusLiveWin32Evidence";

static void draw_line(HDC dc, int x, int y, const wchar_t *text) {
    TextOutW(dc, x, y, text, (int)wcslen(text));
}

static LRESULT CALLBACK window_proc(HWND window, UINT message, WPARAM wparam, LPARAM lparam) {
    switch (message) {
    case WM_CREATE:
        SetTimer(window, 1, 500, NULL);
        return 0;
    case WM_TIMER: {
        ++frame_number;
        wchar_t title[96];
        _snwprintf(title, 95, L"Nexus Win32 live app - tick %lu", frame_number);
        title[95] = L'\0';
        SetWindowTextW(window, title);
        InvalidateRect(window, NULL, TRUE);
        return 0;
    }
    case WM_PAINT: {
        PAINTSTRUCT paint;
        HDC dc = BeginPaint(window, &paint);
        RECT bounds;
        GetClientRect(window, &bounds);
        HBRUSH background = CreateSolidBrush(RGB(11, 15, 25));
        FillRect(dc, &bounds, background);
        DeleteObject(background);

        SetBkMode(dc, TRANSPARENT);
        SetTextColor(dc, RGB(0, 240, 255));
        HFONT title_font = CreateFontW(-34, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE,
            DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
            DEFAULT_PITCH | FF_SWISS, L"Segoe UI");
        HFONT body_font = CreateFontW(-23, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
            DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
            DEFAULT_PITCH | FF_SWISS, L"Segoe UI");
        HFONT previous = (HFONT)SelectObject(dc, title_font);
        draw_line(dc, 54, 48, L"NEXUS  /  WINDOWS PE");
        SelectObject(dc, body_font);
        SetTextColor(dc, RGB(237, 247, 255));
        draw_line(dc, 54, 126, L"Native Win32 application is running");
        wchar_t state[96];
        _snwprintf(state, 95, L"Live timer ticks: %lu", frame_number);
        state[95] = L'\0';
        draw_line(dc, 54, 188, state);
        SetTextColor(dc, RGB(159, 180, 201));
        draw_line(dc, 54, 250, L"Built with MinGW-w64; dispatched by nexus-omniloader + Wine");
        SelectObject(dc, previous);
        DeleteObject(title_font);
        DeleteObject(body_font);
        EndPaint(window, &paint);
        return 0;
    }
    case WM_DESTROY:
        KillTimer(window, 1);
        PostQuitMessage(0);
        return 0;
    default:
        return DefWindowProcW(window, message, wparam, lparam);
    }
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR command_line, int show) {
    (void)previous;
    (void)command_line;
    WNDCLASSW wc = {0};
    wc.lpfnWndProc = window_proc;
    wc.hInstance = instance;
    wc.hCursor = LoadCursorW(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.lpszClassName = window_class;
    if (!RegisterClassW(&wc)) return 2;
    HWND window = CreateWindowExW(0, window_class, L"Nexus Win32 live app - starting",
        WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT, 920, 430,
        NULL, NULL, instance, NULL);
    if (!window) return 3;
    ShowWindow(window, show);
    UpdateWindow(window);
    MSG message;
    while (GetMessageW(&message, NULL, 0, 0) > 0) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    return (int)message.wParam;
}
