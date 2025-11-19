
document.addEventListener("DOMContentLoaded", () => {
    const location = window.location.search
    const params = new URLSearchParams(location);
    const dir = params.get('dir');
    fetch(`./${dir}/metadata.json`)
        .then(response => {
            if (!response.ok) {
                throw new Error("ネットワークエラー: " + response.status);
            }
            return response.json();
        })
        .then(data => {
            const titleEle = document.getElementById("title");
            titleEle.textContent = data["title"]

            const releasedEle = document.getElementById("released");
            releasedEle.textContent = data["released_at_j"]

            const itemContainer = document.getElementById("index_link");
            items = data["files"]
            items.forEach(item => {
                // <li>要素生成
                const li = document.createElement("li");
                const a = document.createElement("a");
                a.href = `#${item.id}`
                a.textContent = `${item.title}`
                li.appendChild(a);
                itemContainer.appendChild(li);
            });
            
            const picturesContainer = document.getElementById("pictures");
            items.forEach(item => {
                // <li>要素生成
                const p = document.createElement("p");
                const a = document.createElement("a");
                a.href = `/${dir}/${item.name}`
                a.target = "_blank";
                a.id = item.id
                a.textContent = `${item.title}`
                p.appendChild(a);

                const img = document.createElement("img");
                img.style="border: 2px solid black;"
                img.setAttribute("width", "100%");
                img.setAttribute("height", "auto");
                img.src=`/${dir}/${item.name}`
                p.appendChild(img)


                const to_top_a = document.createElement("a");
                to_top_a.href="#top"
                to_top_a.textContent="ページトップ"
                p.appendChild(to_top_a)

                picturesContainer.appendChild(p)
            });

        })
        .catch(error => {
            console.error("データ取得エラー:", error);
        });
});
