import { redirect } from "next/navigation";

export default async function Page() {
    // 将 /sessions 重定向到 /
    return redirect('/')
}