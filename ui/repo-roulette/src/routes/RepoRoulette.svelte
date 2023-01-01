<script>
// @ts-nocheck
	let email = '';
	let commits = [];
    let commitsFetched = false;
	let loadedDependencies = [];
	const requiredScripts = ['winwheel', 'tweenmax', 'data'];

	let selectedRepo = '';
	let selectedCommit = '';
    let visibleWheel = ''

	let repoWheel = null;
	let commitWheel = null;
	const colourWheel = [
		'#ee1c24',
		'#3cb878',
		'#f6989d',
		'#00aef0',
		'#f26522',
		'#e70697',
		'#fff200',
		'#f6989d'
	];

    function initializeComponent(){
        commitsFetched = false;
        commits = [];
        selectedRepo = null;
        selectedCommit = null;
        repoWheel = null;
	    commitWheel = null;
        visibleWheel = ''
    }

	function onDependencyLoaded(key) {
		loadedDependencies.push(key);
		let ready = true;
		requiredScripts.forEach((key) => {
			if (!loadedDependencies.includes(key)) {
				ready = false;
			}
		});
		if (ready) {
			repoWheelInit();
		}
	}

	function onRepoSpinResult(indicatedSegment) {
        if(indicatedSegment && indicatedSegment.text && indicatedSegment.text.length > 0){
		    selectedRepo = indicatedSegment.text;
            commitWheelInit()
        }
	}

    function onCommitSpinResult(indicatedSegment) {
        if(indicatedSegment && indicatedSegment.text && indicatedSegment.text.length > 0){
		    selectedCommit = commits.filter(c => c.hash.startsWith(indicatedSegment.text))[0]
        }
	}

	async function fetchRepos() {
		await fetch(`/api/commits/by/author?email=${email}`)
			.then((r) => r.json())
			.then((resp) => {
				commits = resp.data;
                commitsFetched = true
				onDependencyLoaded('data');
			});
	}

	function startRepoWheelSpin() {
		repoWheel.startAnimation();
	}

	function startCommitWheelSpin() {
		commitWheel.startAnimation();
	}


	function getColour(index) {
		while (index > colourWheel.length) index -= colourWheel.length;
		return colourWheel[index];
	}

	function commitToRepoWheelSegment(commit, index) {
		let parts = commit.repo_url.split('/');
		let text = `${parts[parts.length - 1]}`;
		return { text: text, textFontSize: 16, fillStyle: getColour(index) };
	}

    function commitToCommitWheelSegment(commit, index) {
        const text = commit.hash.substring(0,7) // shorten the hash
		return { text: text, textFontSize: 12, fillStyle: getColour(index) };
	}

	const uniqBy = (arr, predicate) => {
		const cb = typeof predicate === 'function' ? predicate : (o) => o[predicate];
		return [
			...arr
				.reduce((map, item) => {
					const key = item === null || item === undefined ? item : cb(item);
					map.has(key) || map.set(key, item);
					return map;
				}, new Map())
				.values()
		];
	};

    function initializeWheel(canvasId, wheelSegments, resultCallback){
        const wheel = new Winwheel({
			canvasId: canvasId,
			outerRadius: 300, // Set outer radius so wheel fits inside the background.
			innerRadius: 50, // Make wheel hollow so segments dont go all way to center.
			textFontSize: 24, // Set default font size for the segments.
			textOrientation: 'horizontal', // Make text vertial so goes down from the outside of wheel.
			textAlignment: 'outer', // Align text to outside of wheel.
			numSegments: wheelSegments.length, // Specify number of segments.
			pointerAngle: 90,
			segments: wheelSegments, // Define segments including colour and text.
			// Specify the animation to use.
			animation: {
				type: 'spinToStop',
				duration: 5,
				spins: 3,
				callbackFinished: resultCallback // Function to call whent the spinning has stopped.
			},
			// Specify pointer guide properties.
			pointerGuide: {
				display: true,
				strokeStyle: 'black',
				lineWidth: 2
			},
			// Turn pins on.
			pins: {
				number: wheelSegments.length,
				fillStyle: 'silver',
				outerRadius: 6
			}
		});

        return wheel
    }


	function repoWheelInit() {
		let commitsOnWheel = [...commits];
		commitsOnWheel = uniqBy(commitsOnWheel, 'repo_url');
		if (commitsOnWheel.length > 30) {
			const shuffled = commitsOnWheel.sort(() => 0.5 - Math.random());
			commitsOnWheel = shuffled.slice(0, 30);
		}

		let wheelSegments = commitsOnWheel.map((c, i) => commitToRepoWheelSegment(c, i));
		repoWheel = initializeWheel('repoWheel', wheelSegments, onRepoSpinResult)
        visibleWheel = 'repoWheel'
	}


    function commitWheelInit() {
		let commitsOnWheel = [...commits];
        commitsOnWheel = commitsOnWheel.filter(c => c.repo_url.includes(selectedRepo))

		if (commitsOnWheel.length > 30) {
			const shuffled = commitsOnWheel.sort(() => 0.5 - Math.random());
			commitsOnWheel = shuffled.slice(0, 30);
		}

		let wheelSegments = commitsOnWheel.map((c, i) => commitToCommitWheelSegment(c, i));
        commitWheel = initializeWheel('commitWheel', wheelSegments, onCommitSpinResult)
        visibleWheel = 'commitWheel'
	}
</script>

<svelte:head>
	<script
		src="https://cdn.jsdelivr.net/npm/winwheeljs@2.7.0/dist/Winwheel.js"
		on:load={onDependencyLoaded('winwheel')}
	></script>
	<script
		src="http://cdnjs.cloudflare.com/ajax/libs/gsap/latest/TweenMax.min.js"
		on:load={onDependencyLoaded('tweenmax')}
	></script>
</svelte:head>
<div>
	<label for="emailInput">Enter email:</label>
    <input id="emailInput" bind:value={email} on:input={initializeComponent}>
	<button on:click={fetchRepos}> Fetch repos </button>
	<button on:click={initializeComponent}> Reset </button>
</div>

{#if commitsFetched == true && commits.length == 0}
<p>No commits for: <strong>{email}</strong></p>
{/if}

<div class:hide={commits.length == 0 || !repoWheel || !repoWheel.ctx || visibleWheel == 'commitWheel'}>
	<button on:click={startRepoWheelSpin}> Spin the wheel </button>

	<canvas id="repoWheel" width="640" height="640">
		Canvas not supported, use another browser.
	</canvas>
</div>

<div class:hide={commits.length == 0 ||!commitWheel || !commitWheel.ctx || visibleWheel == 'repoWheel' }>
	{#if selectedRepo}
		<p>Selected Repo: <strong>{selectedRepo}</strong></p>
	{/if}

	<button on:click={startCommitWheelSpin}> Spin the wheel </button>
    
	<canvas id="commitWheel" width="640" height="640">
		Canvas not supported, use another browser.
	</canvas>
	{#if selectedCommit && selectedCommit.hash}
		<p>Selected Commit:
        <table>
            <tbody>
                <tr>
                    <td>Message</td>
                    <td>{selectedCommit.message.trim()}</td>

                </tr>
                <tr>
                    <td>Summary</td>
                    <td>{selectedCommit.summary.trim()}</td>
                </tr>
                <tr>
                    <td>Author</td>
                    <td>{selectedCommit.author}</td>
                <tr>
                <tr>
                    <td>Date</td>
                    <td>{selectedCommit.date}</td>

                </tr>
                <tr>
                    <td>Diff</td>
                    <td><a href={selectedCommit.diff_link} target="_blank" rel="noreferrer">{selectedCommit.diff_link}</a></td>

                </tr>
                <tr>
                    <td>Email</td>
                    <td>{selectedCommit.email}</td>

                </tr>
            </tbody>
        </table>
	{/if}
</div>

<style>
	.hide {
		display: none !important;
	}
</style>
