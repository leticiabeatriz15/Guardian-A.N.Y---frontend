const API_URL = "https://guardian-a-n-y-backend.onrender.com/analisar";;

// Seletores do DOM
const videoGrid = document.getElementById("videoGrid");
const emptyState = document.getElementById("emptyState");
const searchBar = document.getElementById("searchBar");
const filterSelect = document.getElementById("filterSelect");
const formAnalise = document.getElementById("formAnalise");
const statusAnalise = document.getElementById("statusAnalise");
const btnAnalisar = document.getElementById("btnAnalisar");

let datasetVideos = [];

// Obtém Thumbnail HD do YouTube
function obterThumbnailYoutube(url) {
    let videoId = "";
    if (url.includes("youtu.be/")) {
        videoId = url.split("youtu.be/")[1].split("?")[0];
    } else if (url.includes("watch?v=")) {
        videoId = url.split("watch?v=")[1].split("&")[0];
    }
    return videoId ? `https://img.youtube.com/vi/${videoId}/hqdefault.jpg` : 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500';
}

// Estilo visual dos cards conforme o nível de estímulo
function obterEstiloCard(classificacao) {
    const classeBadgeBase = "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm";
    
    switch((classificacao || "").toUpperCase()) {
        case "HIPERESTIMULANTE":
            return {
                bgCard: "bg-[#FB8A57] border-red-300/60",
                badge: `${classeBadgeBase} bg-red-950/20 text-slate-900 border border-red-900/20`,
                icone: "fa-bolt"
            };
        case "BAIXO ESTÍMULO":
            return {
                bgCard: "bg-[#7ACE9A] border-emerald-300/60",
                badge: `${classeBadgeBase} bg-emerald-950/20 text-slate-900 border border-emerald-900/20`,
                icone: "fa-leaf"
            };
        default:
            return {
                bgCard: "bg-[#FFEB87] border-amber-300/60",
                badge: `${classeBadgeBase} bg-amber-950/20 text-slate-900 border border-amber-900/20`,
                icone: "fa-eye"
            };
    }
}

// Carrega o JSON inicial do dataset
async function carregarVideos() {
    try {
        const resposta = await fetch("dataset_front.json");
        datasetVideos = await resposta.json();

        atualizarDashboard(datasetVideos);
        renderizarGrid(datasetVideos);
    } catch (erro) {
        console.error("Erro ao carregar dataset inicial:", erro);
    }
}

// Renderiza a lista de cards no HTML
function renderizarGrid(videos) {
    videoGrid.innerHTML = "";
    
    if(videos.length === 0) {
        emptyState.classList.remove("hidden");
        return;
    }
    emptyState.classList.add("hidden");

    videos.forEach(video => {
        const thumbUrl = obterThumbnailYoutube(video.url);
        const estilo = obterEstiloCard(video.classificacao);

        const cardHTML = `
            <a href="${video.url}" target="_blank"
            class="group ${estilo.bgCard} rounded-xl overflow-hidden border shadow-sm hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1 flex flex-col">

                <div class="relative aspect-video w-full overflow-hidden bg-black/10">
                    <img src="${thumbUrl}"
                        class="w-full h-full object-cover scale-[1.35] group-hover:scale-[1.40] transition-transform duration-500">

                    <div class="absolute inset-0 bg-slate-900/30 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                        <div class="bg-slate-900/80 text-white w-12 h-12 rounded-full flex items-center justify-center shadow-lg">
                            <i class="fa-solid fa-play text-white ml-1"></i>
                        </div>
                    </div>
                </div>

                <div class="p-4 flex flex-col gap-3 flex-grow justify-between">

                    <h3 class="text-sm font-bold text-slate-900 line-clamp-2 leading-snug">
                        ${video.titulo}
                    </h3>

                    <div>
                        <p class="text-[12px] text-slate-700 font-semibold mb-1 uppercase tracking-wider">
                            Classificação
                        </p>

                        <span class="${estilo.badge}">
                            <i class="fa-solid ${estilo.icone}"></i>
                            ${video.classificacao}
                        </span>
                    </div>

                </div>

            </a>
            `;
        videoGrid.insertAdjacentHTML("beforeend", cardHTML);
    });
}

// Atualiza o painel de métricas no topo
function atualizarDashboard(videos){
    document.getElementById("totalCount").innerText = videos.length;

    document.getElementById("hiperCount").innerText =
        videos.filter(v => (v.classificacao || "").toUpperCase() === "HIPERESTIMULANTE").length;

    document.getElementById("moderadoCount").innerText =
        videos.filter(v => (v.classificacao || "").toUpperCase() === "ESTÍMULO MODERADO").length;

    document.getElementById("baixoCount").innerText =
        videos.filter(v => (v.classificacao || "").toUpperCase() === "BAIXO ESTÍMULO").length;
}

// Filtra vídeos por texto ou categoria
function filtrarVideos() {
    const termoBusca = searchBar.value.toLowerCase();
    const filtroSelecionado = filterSelect.value;

    const videosFiltrados = datasetVideos.filter(video => {
        const bateBusca = video.titulo.toLowerCase().includes(termoBusca);
        const bateFiltro =
            filtroSelecionado === "todos" ||
            (video.classificacao || "").toUpperCase() === filtroSelecionado.toUpperCase();
        return bateBusca && bateFiltro;
    });

    renderizarGrid(videosFiltrados);
}

// Envia a URL para análise via API FastAPI
formAnalise.addEventListener("submit", async (e) => {
    e.preventDefault();
    const inputUrl = document.getElementById("inputUrl");
    const url = inputUrl.value.trim();

    if (!url) return;

    // Feedback visual
    btnAnalisar.disabled = true;
    btnAnalisar.classList.add("opacity-60", "cursor-not-allowed");
    statusAnalise.classList.remove("hidden", "text-red-600", "text-emerald-700");
    statusAnalise.classList.add("text-amber-700");
    statusAnalise.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analisando frames do vídeo com OpenCV e avaliando no modelo de IA... Aguarde.`;

    try {
        const resposta = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url })
        });

        if (!resposta.ok) {
            const erroData = await resposta.json();
            throw new Error(erroData.detail || "Erro ao processar vídeo.");
        }

        const resultado = await resposta.json();

        // Adiciona o novo vídeo analisado no início da lista
        datasetVideos.unshift({
            titulo: resultado.titulo,
            url: resultado.url,
            classificacao: resultado.classificacao
        });

        // Atualiza a interface
        filtrarVideos();
        atualizarDashboard(datasetVideos);

        statusAnalise.classList.remove("text-amber-700");
        statusAnalise.classList.add("text-emerald-700");
        statusAnalise.innerHTML = `<i class="fa-solid fa-circle-check"></i> Vídeo analisado e classificado como <strong>${resultado.classificacao}</strong>!`;

        inputUrl.value = "";
    } catch (erro) {
        statusAnalise.classList.remove("text-amber-700");
        statusAnalise.classList.add("text-red-600");
        statusAnalise.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> ${erro.message}`;
    } finally {
        btnAnalisar.disabled = false;
        btnAnalisar.classList.remove("opacity-60", "cursor-not-allowed");
    }
});

// Eventos de Busca e Filtro
searchBar.addEventListener("input", filtrarVideos);
filterSelect.addEventListener("change", filtrarVideos);

// Execução Inicial
carregarVideos();