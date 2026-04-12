// 定义页面路由参数
interface PageProps{
    params: Promise<{ id: string }>
}

export default async function Page(
    {params}: PageProps,
) {
    // 从 params 中取出 id
    const { id } = await params
    return (
        <div>会话列表页: {id}</div>
    )
}