import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function updateSession(request: NextRequest) {
    let supabaseResponse = NextResponse.next({
        request,
    });

    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                getAll() {
                    return request.cookies.getAll();
                },
                setAll(cookiesToSet) {
                    cookiesToSet.forEach(({ name, value }) =>
                        request.cookies.set(name, value)
                    );
                    supabaseResponse = NextResponse.next({
                        request,
                    });
                    cookiesToSet.forEach(({ name, value, options }) =>
                        supabaseResponse.cookies.set(name, value, options)
                    );
                },
            },
        }
    );

    const {
        data: { user },
    } = await supabase.auth.getUser();

    // Protect /app and /onboarding routes - require authentication
    if (
        user === null &&
        (request.nextUrl.pathname.startsWith("/app") ||
            request.nextUrl.pathname.startsWith("/onboarding"))
    ) {
        const url = request.nextUrl.clone();
        url.pathname = "/login";
        return NextResponse.redirect(url);
    }

    // Redirect authenticated users away from login/register
    if (
        user &&
        (request.nextUrl.pathname.startsWith("/login") ||
            request.nextUrl.pathname.startsWith("/register"))
    ) {
        const url = request.nextUrl.clone();
        url.pathname = "/app";
        return NextResponse.redirect(url);
    }

    return supabaseResponse;
}
