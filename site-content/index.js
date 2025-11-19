document.addEventListener("DOMContentLoaded", () => {
    fetch("directory_list.json")
        .then(response => {
            if (!response.ok) {
                throw new Error("ネットワークエラー: " + response.status);
            }
            return response.json();
        })
        .then(data => {
            const itemContainer = document.getElementById("item");

            data.forEach(dir => {
                // 年月日・時分を抽出
                const year = dir.slice(0, 4);
                const month = dir.slice(4, 6);
                const day = dir.slice(6, 8);
                const hour = dir.slice(9, 11);
                const min = dir.slice(11, 13);

                // タイムスタンプ文字列
                const timeStampStr = `${year}年${month}月${day}日 ${hour}時${min}分`;

                // タイトル判定
                let title;
                if (dir.endsWith("00")) {
                    title = `${timeStampStr} 週間天気予報解説資料`;
                } else {
                    title = `${timeStampStr} 短期予報解説資料`;
                }
                // <li>要素生成
                const li = document.createElement("li");
                const a = document.createElement("a");
                a.href = `viewer.html?dir=${dir}`;
                a.target = "_blank";
                a.textContent = title;

                li.appendChild(a);
                itemContainer.appendChild(li);
            });
        })
        .catch(error => {
            console.error("データ取得エラー:", error);
        });
});
